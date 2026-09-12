"""
uploader.py — YouTube Studio upload automation via Playwright.

Each call to upload_video() will:
  1. Launch a FRESH persistent Chrome context for the language's profile.
  2. Navigate to YouTube Studio (verifies the profile is signed in).
  3. Upload the MP4 file.
  4. Fill in title, description, and tags with human-like typing.
  5. Set audience to "Not made for kids".
  6. Step through the wizard to the Visibility tab.
  7. Select "Schedule", enter the date and time.
  8. Click the final Schedule button and confirm.
  9. CLOSE the context completely.

IMPORTANT: The target Chrome profile must NOT be open in any other Chrome
window when this script runs — Chrome does not allow two processes to share
a profile directory simultaneously.
"""

import logging
import random
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import (
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeout,
    sync_playwright,
)

from config import (
    BROWSER_ARGS,
    BROWSER_SLOW_MO_MS,
    CHROME_PROFILES,
    CHROME_USER_DATA_DIR,
    NAV_TIMEOUT_MS,
    SELECTOR_TIMEOUT_MS,
    UPLOAD_TIMEOUT_MS,
)
from scheduler import format_scheduled_time_for_yt
from utils import human_sleep, slow_type

logger = logging.getLogger(__name__)

STUDIO_URL = "https://studio.youtube.com"


# ─── Selector Registry ────────────────────────────────────────────────────────
# Isolate all CSS selectors here — update only this block when YT Studio
# changes its DOM, without touching any logic elsewhere.

class SEL:
    # Top-bar
    CREATE_BTN        = "#create-icon"
    CREATE_BTN_ALT    = 'button[aria-label="Create"]'
    UPLOAD_ITEM       = "ytcp-upload-btn"
    UPLOAD_ITEM_TEXT  = 'tp-yt-paper-item:has-text("Upload")'

    # Upload dialog
    FILE_INPUT        = 'input[type="file"]'
    UPLOAD_PROGRESS   = "ytcp-video-upload-progress"

    # Details step fields
    TITLE_FIELD       = '#title-textarea div[contenteditable="true"]'
    DESC_FIELD        = '#description-textarea div[contenteditable="true"]'
    SHOW_MORE_BTN = (
        '#toggle-button, '
        'ytcp-button:has-text("Show more"), '
        'ytcp-button:has-text("عرض المزيد"), '
        'ytcp-button:has-text("Mostrar")'
    )
    # Tags
    TAGS_INPUT = (
        'ytcp-form-input-container[label="Tags"] input, '
        'ytcp-form-input-container[label="العلامات"] input, '
        'ytcp-form-input-container[label="Etiquetas"] input, '
        'ytcp-form-input-container input#text-input'
    )
    TAGS_INPUT_ALT = "#text-input"            # fallback inside tag container

    # Audience
    NOT_KIDS_RADIO = (
        'tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT"], '
        'tp-yt-paper-radio-button[name="NOT_MADE_FOR_KIDS"], '
        'tp-yt-paper-radio-button:has-text("not made for kids"), '
        'tp-yt-paper-radio-button:has-text("ليس مخصص"), '
        'tp-yt-paper-radio-button:has-text("no es contenido"), '
        'tp-yt-paper-radio-button:has-text("não é conteúdo")'
    )

    # Wizard navigation
    NEXT_BTN          = 'ytcp-button[id="next-button"]'

    # Visibility step
    SCHEDULE_RADIO = (
        'tp-yt-paper-radio-button[name="SCHEDULE"]',
        '#schedule-radio-button',
        '#second-container-radio-button',
        'text="Schedule"',
        'text="ضبط موعد"',
        'text="Programar"'
    )

    DATE_INPUT = '#datepicker-trigger input, ytcp-date-picker input, input[aria-haspopup="listbox"]:nth-of-type(1)'
    TIME_INPUT = '#time-of-day-trigger input, ytcp-time-of-day-picker input, input[aria-haspopup="listbox"]:nth-of-type(2)'
    DONE_BTN   = 'ytcp-button[id="done-button"]'

    # Post-schedule confirmation
    PROCESSING_DIALOG = "ytcp-uploads-still-processing-dialog"
    CLOSE_BTN         = 'ytcp-button[id="close-button"]'


# ─── Low-level Interaction Helpers ───────────────────────────────────────────

def _wait(page: Page, selector: str, timeout: int = SELECTOR_TIMEOUT_MS) -> None:
    page.wait_for_selector(selector, state="attached", timeout=timeout)
    try:
        page.locator(selector).first.scroll_into_view_if_needed(timeout=2_000)
    except Exception:
        pass


def _click(page: Page, selector: str, timeout: int = SELECTOR_TIMEOUT_MS) -> None:
    human_sleep(0.5, 1.6)
    _wait(page, selector, timeout)
    try:
        page.click(selector, force=True, timeout=3_000)
    except Exception:
        page.evaluate("(sel) => { const el = document.querySelector(sel); if(el) el.click(); }", selector)
    logger.debug("Clicked: %s", selector)


def _try_click(page: Page, *selectors: str, timeout: int = 2_000) -> bool:
    """Try each selector in order; click the first visible one. Returns True on success."""
    for sel in selectors:
        try:
            page.wait_for_selector(sel, state="attached", timeout=1_500)
            page.locator(sel).first.scroll_into_view_if_needed(timeout=2_000)
            human_sleep(0.3, 0.9)
            page.click(sel, force=True)
            logger.debug("Clicked (tried): %s", sel)
            return True
        except Exception:
            continue
    return False


def _clear_and_type(page: Page, selector: str, text: str) -> None:
    """Select all existing content in a field and type replacement text."""
    human_sleep(0.3, 0.9)
    _wait(page, selector)
    page.click(selector)
    page.keyboard.press("Control+a")
    human_sleep(0.1, 0.3)
    page.keyboard.press("Delete")
    human_sleep(0.2, 0.5)
    slow_type(page, selector, text)


def _paste_text(page: Page, selector: str, text: str) -> None:
    """Click a field, select-all, then fill instantly (good for long descriptions)."""
    human_sleep(0.5, 1.2)
    _wait(page, selector)
    page.click(selector)
    page.keyboard.press("Control+a")
    human_sleep(0.1, 0.3)
    page.fill(selector, text)


# ─── Upload Steps ─────────────────────────────────────────────────────────────

def _navigate_to_studio(page: Page) -> None:
    logger.info("Navigating to YouTube Studio…")
    page.goto(STUDIO_URL, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
    human_sleep(3.0, 5.0)

    # Detect redirect to Google sign-in (profile not authenticated)
    if "accounts.google.com" in page.url or "signin" in page.url:
        raise RuntimeError(
            "Redirected to Google Sign-In. "
            "Please sign in manually in this Chrome profile first, then re-run."
        )

    # Just wait a moment for the JavaScript layout to settle
    human_sleep(2.0, 3.0)
    logger.info("YouTube Studio loaded.")


def _open_upload_dialog(page: Page) -> None:
    logger.info("Opening upload dialog…")

    # 1. First, check if there's a huge "Upload videos" button in the empty dashboard center
    big_upload_btn = '#upload-btn, ytcp-button:has-text("Upload videos"), ytcp-button:has-text("تحميل")'
    
    if _try_click(page, big_upload_btn, timeout=4_000):
        logger.info("Clicked the main Dashboard Upload button.")
    else:
        # 2. Fallback to top-right "Create" button
        create_btn_selectors = [
            SEL.CREATE_BTN,
            SEL.CREATE_BTN_ALT,
            "ytcp-button:has-text('Create')",
            "ytcp-button:has-text('إنشاء')",
            "ytcp-button:has-text('Crear')",
            "ytcp-button:has-text('Criar')"
        ]
        if not _try_click(page, *create_btn_selectors, timeout=8_000):
            raise RuntimeError("CREATE button not found on YouTube Studio.")

        human_sleep(0.8, 1.8)

        # "Upload videos" dropdown item
        dropdown_upload_selectors = [
            SEL.UPLOAD_ITEM,
            SEL.UPLOAD_ITEM_TEXT,
            'tp-yt-paper-item:has-text("تحميل")',
            'tp-yt-paper-item:has-text("Subir")',
            'tp-yt-paper-item:has-text("Enviar")'
        ]
        if not _try_click(page, *dropdown_upload_selectors, timeout=8_000):
            raise RuntimeError("'Upload videos' menu item not found in dropdown.")

    # Wait for the file dialog to pop up
    try:
        # Reduced from 60 seconds because expect_file_chooser waits natively
        page.wait_for_selector("ytcp-uploads-dialog", state="visible", timeout=5_000)
    except Exception:
        pass # It might still work, expect_file_chooser handles the rest
    logger.info("Upload dialog open.")


def _set_video_file(page: Page, video_path: Path) -> None:
    logger.info("Setting file: %s", video_path.name)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    # Use expect_file_chooser which intercepts the actual OS popup without caring about hidden inputs!
    select_files_btn = 'ytcp-button:has-text("Select files"), ytcp-button:has-text("اختيار ملفات"), #select-files-button'
    
    with page.expect_file_chooser(timeout=30_000) as fc_info:
        human_sleep(0.5, 1.5)
        page.click(select_files_btn)

    file_chooser = fc_info.value
    file_chooser.set_files(str(video_path))
    human_sleep(3.0, 5.0)

    try:
        _wait(page, SEL.UPLOAD_PROGRESS, timeout=30_000)
        logger.info("Upload progress bar detected — upload underway.")
    except PlaywrightTimeout:
        logger.warning("Upload progress bar not detected within 30s — proceeding.")


def _fill_details(page: Page, metadata: dict) -> None:
    """Fill title, description, and tags fields."""

    # Title
    logger.info("Typing title…")
    _clear_and_type(page, SEL.TITLE_FIELD, metadata["title"])
    human_sleep(0.5, 1.2)
    # The title often ends with `#Shorts`, triggering the hashtag dropdown.
    page.keyboard.press("Escape")
    human_sleep(0.3, 0.5)

    # Description
    logger.info("Pasting description…")
    _paste_text(page, SEL.DESC_FIELD, metadata["description"])
    human_sleep(0.6, 1.4)
    # Description might also trigger dropdowns, so try closing again.
    page.keyboard.press("Escape")
    human_sleep(0.2, 0.5)
    # Give the box time to expand if needed
    page.keyboard.press("Tab") 
    human_sleep(1.0, 2.0)

    # YouTube lazy-loads the lower elements (Audience, Tags). We MUST scroll to trigger them!
    logger.info("Scrolling down to reveal lazy-loaded elements…")
    page.mouse.move(x=400, y=400) # Hover over modal
    for _ in range(3):
        page.mouse.wheel(delta_y=800, delta_x=0)
        human_sleep(0.5, 1.2)
        page.keyboard.press("PageDown") # Fallback scroll if mouse wheel misses

    # Tags — reveal via "Show more" then type each tag + comma
    logger.info("Filling tags…")
    try:
        page.wait_for_selector(SEL.SHOW_MORE_BTN, state="attached", timeout=6_000)
        page.locator(SEL.SHOW_MORE_BTN).first.scroll_into_view_if_needed(timeout=2_000)
        human_sleep(0.4, 0.9)
        page.click(SEL.SHOW_MORE_BTN, force=True)
        human_sleep(0.8, 1.6)
    except Exception:
        logger.debug("'Show more' not found or failed — tags section may already be visible.")

    tags_sel: str | None = None
    for sel in (SEL.TAGS_INPUT, SEL.TAGS_INPUT_ALT):
        try:
            page.wait_for_selector(sel, state="attached", timeout=8_000)
            page.locator(sel).first.scroll_into_view_if_needed(timeout=2_000)
            tags_sel = sel
            break
        except Exception:
            continue

    if tags_sel:
        page.click(tags_sel)
        for tag in metadata.get("tags", []):
            tag = tag.strip()
            if not tag:
                continue
            human_sleep(0.1, 0.4)
            page.type(tags_sel, tag + ",", delay=random.randint(60, 130))
        human_sleep(0.5, 1.0)
        logger.info("Tags filled.")
    else:
        logger.warning("Tags input not found — skipping tags.")


def _set_audience(page: Page) -> None:
    logger.info("Setting audience to 'Not made for kids'…")
    _click(page, SEL.NOT_KIDS_RADIO)
    human_sleep(0.5, 1.2)


def _click_next(page: Page, step_label: str) -> None:
    """Click NEXT, waiting first for the button to become enabled."""
    logger.info("Clicking NEXT from step: %s", step_label)
    human_sleep(0.8, 2.0)

    # Wait for NEXT to be interactive (upload may still be in progress)
    try:
        page.wait_for_function(
            """() => {
                const btn = document.querySelector('ytcp-button#next-button');
                return btn && !btn.hasAttribute('disabled');
            }""",
            timeout=UPLOAD_TIMEOUT_MS,
        )
    except PlaywrightTimeout:
        logger.warning("NEXT button still disabled after timeout — clicking anyway.")

    _click(page, SEL.NEXT_BTN)
    human_sleep(1.5, 3.0)


def _advance_to_visibility(page: Page) -> None:
    """Click through Details → Video elements → Checks → Visibility."""
    _click_next(page, "Details")
    _click_next(page, "Video elements")
    _click_next(page, "Checks")
    logger.info("Reached Visibility step.")


def _set_schedule(page: Page, scheduled_time: datetime) -> None:
    """Select the Schedule radio and enter the date and time."""
    date_str, time_str = format_scheduled_time_for_yt(scheduled_time)
    logger.info("Scheduling: date=%s  time=%s", date_str, time_str)

    success = _try_click(page, *SEL.SCHEDULE_RADIO, timeout=8_000)
    if not success:
        logger.warning("Could not find the Schedule button via any known selector.")
    
    human_sleep(1.0, 2.0)

    # Date field
    date_locators = (
        'ytcp-date-picker input',
        '#datepicker-trigger input',
        '#datepicker-trigger',
        'input[aria-haspopup="listbox"]:nth-of-type(1)'
    )
    date_success = False
    for sel in date_locators:
        try:
            page.wait_for_selector(sel, state="attached", timeout=2_000)
            page.locator(sel).first.scroll_into_view_if_needed(timeout=2_000)
            page.click(sel, force=True)
            human_sleep(0.4, 0.8)
            # Some inputs need triple click, some just need Control+A
            page.keyboard.press("Control+a")
            human_sleep(0.2, 0.5)
            page.keyboard.type(date_str, delay=random.randint(60, 110))
            page.keyboard.press("Enter")
            page.keyboard.press("Tab")
            logger.info("Date entered: %s (via %s)", date_str, sel)
            date_success = True
            break
        except Exception:
            continue
            
    if not date_success:
        raise RuntimeError("Date picker not found via any known selector.")

    human_sleep(0.5, 1.0)

    # Time field
    time_locators = (
        '#time-of-day-trigger input',
        '#time-of-day-trigger',
        'ytcp-time-of-day-picker input',
        'input:right-of(#datepicker-trigger)',
        'input:right-of(ytcp-date-picker)'
    )
    time_success = False
    for sel in time_locators:
        try:
            page.wait_for_selector(sel, state="attached", timeout=2_000)
            # if we find it, try to focus and click
            page.click(sel, force=True)
            human_sleep(0.4, 0.8)
            page.keyboard.press("Control+a")
            human_sleep(0.2, 0.5)
            # we don't type ':' because it causes bugs in some YT versions, just sending the keys
            page.keyboard.type(time_str, delay=random.randint(60, 110))
            page.keyboard.press("Enter")
            page.keyboard.press("Tab")
            logger.info("Time entered: %s (via %s)", time_str, sel)
            time_success = True
            break
        except Exception:
            continue
            
    if not time_success:
        raise RuntimeError("Time picker not found via any known selector.")

    human_sleep(0.8, 1.5)


def _wait_for_upload_completion(page: Page) -> None:
    """
    Waits for the video file upload to reach 100%. 
    This prevents the browser from closing while the MP4 is still transferring,
    which causes the 'Uploading 81%' stuck state.
    """
    logger.info("Checking if video file is fully uploaded to YouTube servers...")
    
    # We will poll the upload progress footer text
    # As long as it doesn't contain indicating keywords of completion/processing, we wait.
    completion_keywords = [
        "processing", "معالج", "procesando", "processando",
        "complete", "مكتمل", "اكتمل", "complet", "concluíd",
        "check", "تحقق", "verific"
    ]
    
    max_wait = UPLOAD_TIMEOUT_MS / 1000.0
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            progress_el = page.locator(SEL.UPLOAD_PROGRESS).first
            if not progress_el.is_visible():
                logger.info("Upload progress footer not visible. Assuming upload complete.")
                break
                
            text = progress_el.inner_text().lower()
            
            if not text.strip():
                human_sleep(2.0, 3.0)
                continue
                
            is_done = False
            for kw in completion_keywords:
                if kw in text:
                    is_done = True
                    break
            
            if "100%" in text and "uploading" not in text and "تحميل" not in text and "subiendo" not in text and "enviando" not in text:
                 is_done = True

            if is_done:
                logger.info("Upload reached safe checkpoint! Progress text: %r", text.replace('\n', ' '))
                break
                
            logger.info("Still uploading: %r...", text.replace('\n', ' '))
            
        except Exception as e:
            logger.warning("Error reading upload progress: %s. Will retry...", e)
            
        human_sleep(4.0, 6.0)
    else:
        logger.warning("Upload wait timed out! Proceeding anyway...")
        
    human_sleep(2.0, 3.0)


def _confirm_schedule(page: Page) -> None:
    """Click the final SCHEDULE button and wait for confirmation."""
    _wait_for_upload_completion(page)
    logger.info("Clicking final SCHEDULE button…")
    _click(page, SEL.DONE_BTN, timeout=15_000)
    human_sleep(2.5, 4.5)

    # YouTube may show a "still processing" dialog — this is normal for Shorts
    try:
        page.wait_for_selector(SEL.PROCESSING_DIALOG, timeout=20_000)
        logger.info("Processing dialog appeared — schedule confirmed.")
        try:
            page.click(SEL.CLOSE_BTN, timeout=5_000)
        except PlaywrightTimeout:
            pass
    except PlaywrightTimeout:
        logger.info("No processing dialog — schedule accepted silently. URL: %s", page.url)

    human_sleep(1.5, 3.0)


# ─── Main Public Function ─────────────────────────────────────────────────────

def upload_video(
    lang: str,
    video_path: Path,
    metadata: dict,
    scheduled_time: datetime,
    dry_run: bool = False,
) -> bool:
    """
    Execute the full upload pipeline for one language channel.

    Launches the Chrome persistent context for *lang*, runs every upload step,
    closes the context, and returns True on success / False on any failure.

    Args:
        lang:           Language code ("AR", "EN", "ES", "PT").
        video_path:     Absolute Path to the .mp4 file.
        metadata:       Dict with keys "title", "description", "tags".
        scheduled_time: Timezone-aware datetime (Egypt TZ) for YT scheduling.
        dry_run:        If True, no browser is launched — only log the intent.

    Returns:
        bool: True = success, False = failure (caller should handle retry/error).
    """
    if dry_run:
        date_str, time_str = format_scheduled_time_for_yt(scheduled_time)
        logger.info(
            "[DRY-RUN][%s] Would upload '%s' | Title: '%s' | Scheduled: %s %s",
            lang, video_path.name, metadata.get("title", "N/A"), date_str, time_str,
        )
        return True

    profile = CHROME_PROFILES.get(lang)
    if not profile:
        logger.error("No Chrome profile configured for language: %s", lang)
        return False

    logger.info("=== [%s] Launching Chrome '%s' ===", lang, profile)

    context: BrowserContext | None = None
    try:
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=CHROME_USER_DATA_DIR,
                channel="chrome",
                headless=False,
                slow_mo=BROWSER_SLOW_MO_MS,
                args=[f"--profile-directory={profile}"] + BROWSER_ARGS,
                ignore_default_args=["--enable-automation"],
                no_viewport=True,
            )

            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(SELECTOR_TIMEOUT_MS)
            page.set_default_navigation_timeout(NAV_TIMEOUT_MS)

            _navigate_to_studio(page)
            _open_upload_dialog(page)
            _set_video_file(page, video_path)
            _fill_details(page, metadata)
            _set_audience(page)
            _advance_to_visibility(page)
            _set_schedule(page, scheduled_time)
            _confirm_schedule(page)

            logger.info("=== [%s] Upload complete — closing browser. ===", lang)
            context.close()
            return True

    except (RuntimeError, FileNotFoundError) as exc:
        logger.error("[%s] Upload failed: %s", lang, exc)
    except PlaywrightTimeout as exc:
        logger.error("[%s] Timeout during upload: %s", lang, exc)
    except Exception as exc:
        logger.exception("[%s] Unexpected error: %s", lang, exc)
    finally:
        # Guarantee context is closed even if an exception bypassed context.close()
        if context is not None:
            try:
                context.close()
            except Exception:
                pass

    return False
