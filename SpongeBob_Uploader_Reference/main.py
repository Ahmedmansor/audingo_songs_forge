"""
main.py — Orchestrator: scan queue → generate metadata → upload → archive.

Queue Blocking Rule:
    The script scans Upload_Queue alphabetically and LOCKS onto the first
    episode that is not yet 100% successful. No subsequent episode is touched
    until the locked episode reaches full "success" across all languages.
    Gaps in numbering (e.g. missing Ep_03) are naturally skipped.
    Errored languages are auto-retried on every run.

Usage:
    python main.py                      # Auto-lock on first incomplete episode
    python main.py --dry-run            # Simulate: calls Gemini, skips browser
    python main.py --lang AR            # Only process the AR language for locked ep
    python main.py --episode Ep_04      # Override auto-lock to a specific episode
    python main.py --dry-run --lang AR  # Verify AR metadata only
    python main.py --log-level DEBUG    # Verbose logging
"""

import argparse
import logging
import sys
import time

from config import (
    BASE_DIR,
    LANGUAGES,
    LOGS_DIR,
    UPLOAD_QUEUE_DIR,
    UPLOAD_RETRY_COOLDOWN_SEC,
    UPLOADED_DONE_DIR,
)
from metadata_gen import generate_all_metadata
from scheduler import get_next_slot, increment_upload_count
from state_manager import (
    RESUMABLE_STATUSES,
    STATUS_ERROR,
    STATUS_LOADING,
    STATUS_PENDING,
    STATUS_SUCCESS,
    get_episode_summary,
    is_episode_complete,
    load_state,
    set_upload_status,
    sync_state_with_queue,
)
from uploader import upload_video
from utils import ensure_dirs, human_sleep, move_episode_to_done, setup_logging

logger = logging.getLogger(__name__)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="YouTube Shorts Auto-Uploader — Playwright + Gemini AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simulate the run without launching a browser or calling the Gemini API.",
    )
    parser.add_argument(
        "--lang", choices=LANGUAGES, default=None,
        help="Restrict to a single language channel.",
    )
    parser.add_argument(
        "--episode", default=None,
        help="Restrict to a single episode folder name (e.g. Ep_01).",
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO).",
    )
    return parser.parse_args()


# ─── Pre-flight ───────────────────────────────────────────────────────────────

def _pre_flight(dry_run: bool) -> None:
    ensure_dirs(UPLOAD_QUEUE_DIR, UPLOADED_DONE_DIR, LOGS_DIR)
    logger.info("=" * 62)
    logger.info("  YouTube Shorts Auto-Uploader")
    logger.info("  Base dir : %s", BASE_DIR)
    logger.info("  Dry-run  : %s", dry_run)
    logger.info("=" * 62)

    if not UPLOAD_QUEUE_DIR.exists():
        logger.warning("Upload_Queue directory does not exist — creating it.")
        return

    ep_dirs = [p for p in UPLOAD_QUEUE_DIR.iterdir() if p.is_dir()]
    if not ep_dirs:
        logger.warning(
            "Upload_Queue is empty. "
            "Add Ep_XX folders (each with AR/EN/ES/PT.mp4 and script.txt)."
        )


# ─── Metadata Helpers ─────────────────────────────────────────────────────────

def _read_script(episode: str) -> str:
    script_path = UPLOAD_QUEUE_DIR / episode / "script.txt"
    if not script_path.exists():
        raise FileNotFoundError(f"script.txt not found: {script_path}")
    return script_path.read_text(encoding="utf-8")


def _get_metadata(
    episode: str, langs_needed: list[str], dry_run: bool  # dry_run kept for signature compat
) -> dict[str, dict | None]:
    """
    Read script.txt and call Gemini for all needed languages.

    The real Gemini API is ALWAYS called — even in --dry-run mode — so
    the user can verify hook logic and translations before a live upload.
    """
    try:
        script_text = _read_script(episode)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return {lang: None for lang in langs_needed}

    ep_path = UPLOAD_QUEUE_DIR / episode
    logger.info("[%s] Calling Gemini for metadata (langs: %s)…", episode, langs_needed)
    return generate_all_metadata(script_text, episode_path=ep_path, langs=langs_needed)


def _print_metadata_preview(episode: str, all_metadata: dict[str, dict | None]) -> None:
    """
    Pretty-print generated metadata to the console so the user can verify
    the hook interpretations and translations before any real upload happens.
    """
    sep = "─" * 62
    print(f"\n{'═' * 62}")
    print(f"  METADATA PREVIEW — {episode}")
    print(f"{'═' * 62}")
    for lang, meta in all_metadata.items():
        print(f"\n{sep}")
        print(f"  [{lang}]")
        print(sep)
        if meta is None:
            print("  ⚠  Generation FAILED for this language.")
            continue
        print(f"  TITLE       : {meta['title']}")
        print(f"  DESCRIPTION :")
        for line in meta["description"].splitlines():
            print(f"                {line}")
        tags_str = ", ".join(meta.get("tags", []))
        print(f"  TAGS        : {tags_str}")
    print(f"\n{'═' * 62}\n")


# ─── Single-Upload Handler With Retry ─────────────────────────────────────────

def _attempt_upload(
    lang: str,
    episode: str,
    metadata: dict,
    state: dict,
    dry_run: bool,
) -> tuple[bool, dict]:
    """
    Try to upload one (episode, lang) video. Retries once on failure
    after UPLOAD_RETRY_COOLDOWN_SEC seconds. Marks "error" after two failures.

    Returns:
        (success, updated_state)
    """
    video_path = UPLOAD_QUEUE_DIR / episode / f"{lang}.mp4"

    if not video_path.exists() and not dry_run:
        logger.error("[%s][%s] MP4 not found: %s", episode, lang, video_path)
        state = set_upload_status(state, episode, lang, STATUS_ERROR)
        return False, state

    # Compute the scheduled slot BEFORE marking as loading
    scheduled_time, date_key = get_next_slot(lang)

    # Mark in-progress
    state = set_upload_status(state, episode, lang, STATUS_LOADING)

    for attempt in range(1, 3):
        logger.info("[%s][%s] Upload attempt %d / 2…", episode, lang, attempt)

        success = upload_video(
            lang=lang,
            video_path=video_path,
            metadata=metadata,
            scheduled_time=scheduled_time,
            dry_run=dry_run,
        )

        if success:
            state = set_upload_status(state, episode, lang, STATUS_SUCCESS)
            increment_upload_count(lang, date_key)
            return True, state

        if attempt == 1:
            logger.warning(
                "[%s][%s] Attempt 1 failed. Cooling down %ds before retry…",
                episode, lang, UPLOAD_RETRY_COOLDOWN_SEC,
            )
            time.sleep(UPLOAD_RETRY_COOLDOWN_SEC)

    logger.error(
        "[%s][%s] Both attempts failed — marking ERROR.", episode, lang
    )
    state = set_upload_status(state, episode, lang, STATUS_ERROR)
    return False, state


# ─── Queue Lock Helper ────────────────────────────────────────────────────────

def _find_locked_episode(state: dict) -> str | None:
    """
    Scan Upload_Queue alphabetically and return the name of the FIRST episode
    that is NOT yet 100% 'success'.

    Rules:
    - Folders not starting with 'Ep_' are ignored.
    - Gaps in numbering (Ep_01, Ep_02, Ep_04 — no Ep_03) are naturally skipped;
      the script does not wait for or care about missing numbers.
    - Returns None when every queued episode is fully successful.
    """
    if not UPLOAD_QUEUE_DIR.exists():
        return None

    episodes_on_disk = sorted(
        p.name for p in UPLOAD_QUEUE_DIR.iterdir()
        if p.is_dir() and p.name.startswith("Ep_")
    )

    for ep in episodes_on_disk:
        if not is_episode_complete(state, ep):
            logger.debug("[%s] is incomplete — selected as locked episode.", ep)
            return ep

    return None  # All queued episodes are done


# ─── Main Orchestration Loop ─────────────────────────────────────────────────

def main() -> None:
    args = _parse_args()
    setup_logging(getattr(logging, args.log_level))

    _pre_flight(args.dry_run)

    # 1. Load state and sync with whatever is in Upload_Queue on disk
    state = load_state()
    state = sync_state_with_queue(state)

    # 2. Determine the locked episode
    #    --episode flag overrides the auto-lock (useful for debugging / testing)
    if args.episode:
        locked_ep = args.episode
        logger.info("Queue lock OVERRIDDEN by --episode flag: [%s]", locked_ep)
    else:
        locked_ep = _find_locked_episode(state)

    if locked_ep is None:
        logger.info("All queued episodes are fully complete. Nothing to do. Exiting.")
        return

    logger.info(
        "🔒 Locked episode: [%s]  — queue is BLOCKED until this episode reaches "
        "100%% success across all languages.",
        locked_ep,
    )

    # 3. Determine actionable languages for the locked episode
    #    Actionable = pending | loading | error  (all resumable statuses)
    actionable_langs = [
        lang for lang in LANGUAGES
        if state.get(locked_ep, {}).get(lang) in RESUMABLE_STATUSES
    ]

    # Apply optional --lang filter
    if args.lang:
        actionable_langs = [l for l in actionable_langs if l == args.lang]

    if not actionable_langs:
        logger.info(
            "[%s] No actionable languages for the locked episode "
            "(all are already 'success' for the selected filter). Exiting.",
            locked_ep,
        )
        return

    logger.info("[%s] Actionable languages this run: %s", locked_ep, actionable_langs)

    # 4. Generate metadata (Gemini called even in --dry-run for preview)
    all_metadata = _get_metadata(locked_ep, actionable_langs, args.dry_run)
    _print_metadata_preview(locked_ep, all_metadata)

    # 5. Upload each language sequentially (each gets its own Chrome profile)
    for lang in actionable_langs:
        meta = all_metadata.get(lang)

        if meta is None:
            logger.error("[%s][%s] Metadata unavailable — skipping.", locked_ep, lang)
            state = set_upload_status(state, locked_ep, lang, STATUS_ERROR)
            continue

        success, state = _attempt_upload(lang, locked_ep, meta, state, args.dry_run)

        if success:
            logger.info("[%s][%s] ✓ Uploaded successfully.", locked_ep, lang)
            human_sleep(3.0, 7.0)   # brief cooldown between Chrome profile launches
        else:
            logger.warning("[%s][%s] ✗ Upload failed — marked ERROR.", locked_ep, lang)

    # 6. Summarise and archive
    logger.info(get_episode_summary(state, locked_ep))

    if is_episode_complete(state, locked_ep):
        logger.info(
            "[%s] ✅ All languages succeeded! Moving to Uploaded_Done…", locked_ep
        )
        if not args.dry_run:
            move_episode_to_done(UPLOAD_QUEUE_DIR / locked_ep, UPLOADED_DONE_DIR)
        else:
            logger.info("[DRY-RUN][%s] Would move to Uploaded_Done.", locked_ep)
    else:
        still_resumable = [
            l for l in LANGUAGES
            if state.get(locked_ep, {}).get(l) in RESUMABLE_STATUSES
        ]
        logger.warning(
            "[%s] ⛔ Episode still incomplete — queue remains BLOCKED. "
            "Languages still needing attention: %s. Re-run to retry.",
            locked_ep, still_resumable,
        )

    # 7. Final run summary
    logger.info("=" * 62)
    logger.info("Run complete.")
    logger.info(get_episode_summary(state, locked_ep))
    logger.info("=" * 62)


if __name__ == "__main__":
    main()
