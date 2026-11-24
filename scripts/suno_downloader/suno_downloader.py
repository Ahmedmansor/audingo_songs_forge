import os
import re
import sys
import json
import time
import random
import shutil
import base64
import subprocess
from playwright.sync_api import sync_playwright

# ==============================================================================
# CONFIGURATION
# ==============================================================================
CDP_PORT = 9222
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT_DIR = r"C:\Users\ahmedMansour\Downloads\Suno-Audingo"
SONGS_JSON_PATH = os.path.join(BASE_DIR, "songs.json")
MANIFEST_PATH = os.path.join(BASE_DIR, "suno_library_manifest.json")
MIN_AUDIO_SIZE = 500_000

FFMPEG_PATH = shutil.which("ffmpeg")
if not FFMPEG_PATH:
    winget_ffmpeg = r"C:\Users\ahmedMansour\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"
    if os.path.exists(winget_ffmpeg):
        FFMPEG_PATH = winget_ffmpeg

HOOK_JS = """
window.__sb_buffers = window.__sb_buffers || [];
window.__sb_capture = false;

if (!window.__orig_append) {
    window.__orig_append = SourceBuffer.prototype.appendBuffer;
    SourceBuffer.prototype.appendBuffer = function(buf) {
        if (window.__sb_capture && buf) {
            try {
                const u8 = buf instanceof ArrayBuffer ? new Uint8Array(buf) : new Uint8Array(buf.buffer, buf.byteOffset, buf.byteLength);
                window.__sb_buffers.push(u8);
            } catch(e) {}
        }
        return window.__orig_append.apply(this, arguments);
    };
}
"""

def sanitize_filename(name: str) -> str:
    s = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return re.sub(r'[\.\-]+$', '', s).strip()

def load_songs_list():
    if not os.path.exists(SONGS_JSON_PATH):
        print(f"[!] Error: {SONGS_JSON_PATH} not found!")
        return []
    with open(SONGS_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def parse_duration_text(text):
    m = re.search(r'\b(\d+):([0-5]\d)\b', text)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2)), f"{m.group(1)}:{m.group(2)}"
    return 0, ""

def file_is_complete(target_folder: str, clean_title: str, expected_sec: int) -> bool:
    """Checks if file exists and duration matches within 3.0 seconds."""
    m = re.match(r'^(\d+(?:\.\d+)?)-?', clean_title)
    if not m:
        return False
    target_ver = m.group(1)

    for fname in os.listdir(target_folder):
        if not fname.endswith(".m4a") and not fname.endswith(".mp3"):
            continue
        if fname.startswith("_temp"):
            continue
        m_file = re.match(r'^(\d+(?:\.\d+)?)-?', fname)
        if m_file and m_file.group(1) == target_ver:
            fpath = os.path.join(target_folder, fname)
            if os.path.getsize(fpath) < MIN_AUDIO_SIZE:
                return False
            # If expected_sec > 0, verify ffprobe duration
            if expected_sec > 0:
                try:
                    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', fpath]
                    out = subprocess.check_output(cmd, text=True).strip()
                    dur = float(out)
                    if (expected_sec - dur) > 3.0: # truncated by >3 seconds
                        return False
                except Exception:
                    pass
            return True
    return False

def run_downloader():
    print("=" * 80)
    print("   Suno AI High-Fidelity Lossless Stream Downloader (SourceBuffer Driven)")
    print("=" * 80)

    songs = load_songs_list()
    if not songs:
        return

    print(f"[*] Loaded {len(songs)} song(s) from songs.json.")
    print(f"[*] Connecting to Opera on port {CDP_PORT}...")

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP_PORT}")
        except Exception as e:
            print(f"[X] Could not connect to Opera: {e}")
            return

        context = browser.contexts[0]
        context.add_init_script(HOOK_JS)

        page = next((pg for pg in context.pages if "suno.com" in pg.url and "create" in pg.url), None)
        if not page:
            page = context.new_page()
            page.goto("https://suno.com/create", wait_until="domcontentloaded")
            time.sleep(3)

        page.bring_to_front()
        page.evaluate(HOOK_JS)

        total_downloaded = 0
        total_skipped = 0

        for idx, song in enumerate(songs, 1):
            num = str(song.get("number")).strip()
            name = song.get("name", "").strip()
            if not num or not name:
                continue

            folder_num = int(num) if num.isdigit() else num
            cand1 = os.path.join(DEFAULT_OUTPUT_DIR, f"{folder_num:02d}- {name}" if isinstance(folder_num, int) else f"{folder_num}- {name}")
            cand2 = os.path.join(DEFAULT_OUTPUT_DIR, f"{folder_num}- {name}")
            target_folder = cand1 if os.path.exists(cand1) else (cand2 if os.path.exists(cand2) else cand1)
            os.makedirs(target_folder, exist_ok=True)

            print("\n" + "=" * 80)
            print(f"[{idx}/{len(songs)}] Song #{num}: '{name}'")
            print(f"     Folder: {target_folder}")

            # 1. Search song by name
            search_input = page.locator('input[placeholder*="Search" i], input[type="search" i]').first
            search_input.wait_for(state="visible", timeout=10000)
            search_input.fill("")
            search_input.type(name, delay=15)
            search_input.press("Enter")
            time.sleep(1.8)

            for _ in range(3):
                page.mouse.wheel(0, 1500)
                time.sleep(0.3)

            # Query matching clips
            clips = page.evaluate("""(targetNum) => {
                const found = [];
                const regex = new RegExp('^' + targetNum + '(\\\\.\\\\d+)?-?\\\\s*(.+)', 'i');
                const rows = document.querySelectorAll('[data-testid="clip-row"]');
                for (let r of rows) {
                    const aria = (r.getAttribute('aria-label') || '').trim();
                    const txt = r.innerText || '';
                    if (regex.test(aria)) {
                        found.push({ aria: aria, text: txt });
                    }
                }
                return found;
            }""", num)

            # Secondary search by number if needed
            if len(clips) == 0 or num in ["3", "13", "14", "131", "133"]:
                search_input.fill("")
                search_input.type(f"{num}-", delay=15)
                search_input.press("Enter")
                time.sleep(1.5)
                more_clips = page.evaluate("""(targetNum) => {
                    const found = [];
                    const regex = new RegExp('^' + targetNum + '(\\\\.\\\\d+)?-?\\\\s*(.+)', 'i');
                    const rows = document.querySelectorAll('[data-testid="clip-row"]');
                    for (let r of rows) {
                        const aria = (r.getAttribute('aria-label') || '').trim();
                        const txt = r.innerText || '';
                        if (regex.test(aria)) found.push({ aria: aria, text: txt });
                    }
                    return found;
                }""", num)
                existing = {c["aria"] for c in clips}
                for c in more_clips:
                    if c["aria"] not in existing:
                        clips.append(c)

            # For 13 and 14 if still empty
            if len(clips) == 0 and num in ["13", "14"]:
                search_input.fill("")
                search_input.type(f"{num} ", delay=15)
                search_input.press("Enter")
                time.sleep(1.5)
                more_clips = page.evaluate("""(targetNum) => {
                    const found = [];
                    const regex = new RegExp('^' + targetNum + '\\\\s*(.+)', 'i');
                    const rows = document.querySelectorAll('[data-testid="clip-row"]');
                    for (let r of rows) {
                        const aria = (r.getAttribute('aria-label') || '').trim();
                        const txt = r.innerText || '';
                        if (regex.test(aria)) found.push({ aria: aria, text: txt });
                    }
                    return found;
                }""", num)
                existing = {c["aria"] for c in clips}
                for c in more_clips:
                    if c["aria"] not in existing:
                        clips.append(c)

            print(f"     [V] Found {len(clips)} version(s) on Suno.")

            seen_titles = set()
            for c in clips:
                full_title = c["aria"]
                if full_title in seen_titles:
                    continue
                seen_titles.add(full_title)

                clean_title = sanitize_filename(full_title)
                expected_sec, dur_str = parse_duration_text(c["text"])
                dst_m4a = os.path.join(target_folder, f"{clean_title}.m4a")

                # Check if already complete
                if file_is_complete(target_folder, clean_title, expected_sec):
                    print(f"     -> [SKIP] Already complete & verified: '{clean_title}.m4a'")
                    total_skipped += 1
                    continue

                print(f"\n     -> [FETCH] Capturing: '{full_title}' (Suno duration: {dur_str} / {expected_sec}s)")

                # Reset SourceBuffer capture
                page.evaluate("() => { window.__sb_buffers = []; window.__sb_capture = true; }")

                # Trigger Play
                try:
                    btn = page.locator(f'[data-testid="clip-row"][aria-label="{full_title}"] [aria-label^="Play " i]').first
                    if not btn.is_visible(timeout=1500):
                        btn = page.locator(f'[aria-label*="Play {full_title}" i]').first
                    btn.scroll_into_view_if_needed()
                    time.sleep(0.3)
                    btn.click()
                except Exception as e:
                    print(f"        [!] Play click error: {e}")
                    continue

                # Mute
                page.evaluate("() => document.querySelectorAll('audio').forEach(a => a.muted = true)")

                # Seek loop to force 100% buffer
                print("        [*] Seeking through stream to trigger 100% full buffering...")
                for tick in range(24): # up to 12s
                    time.sleep(0.5)
                    st = page.evaluate("""() => {
                        const a = document.querySelector('audio');
                        if (!a) return { done: false, bytes: 0 };
                        if (a.buffered && a.buffered.length > 0 && a.duration) {
                            const last = a.buffered.end(a.buffered.length - 1);
                            if (last < a.duration - 2) {
                                a.currentTime = Math.min(last + 2, a.duration - 0.5);
                            }
                        }
                        const isDone = a.buffered && a.buffered.length > 0 && a.duration && (a.buffered.end(a.buffered.length - 1) >= a.duration - 1);
                        return {
                            done: isDone,
                            bytes: (window.__sb_buffers || []).reduce((acc, b) => acc + b.length, 0),
                            cur: a.currentTime,
                            dur: a.duration
                        };
                    }""")
                    if st.get("done") and st.get("bytes", 0) > 1_000_000:
                        break

                # Stop playback
                page.evaluate("() => { window.__sb_capture = false; document.querySelectorAll('audio').forEach(a => a.pause()); }")

                # Get binary data
                b64 = page.evaluate("""() => {
                    const total = window.__sb_buffers.reduce((acc, b) => acc + b.length, 0);
                    const merged = new Uint8Array(total);
                    let offset = 0;
                    for (let b of window.__sb_buffers) {
                        merged.set(b, offset);
                        offset += b.length;
                    }
                    let bin = '';
                    const len = merged.byteLength;
                    for (let i = 0; i < len; i += 32768) {
                        bin += String.fromCharCode.apply(null, merged.subarray(i, Math.min(i + 32768, len)));
                    }
                    return btoa(bin);
                }""")

                raw_data = base64.b64decode(b64)
                if len(raw_data) < MIN_AUDIO_SIZE:
                    print(f"        [!] Incomplete capture ({len(raw_data):,} bytes). Skipping.")
                    continue

                temp_raw = os.path.join(target_folder, f"_temp_{clean_title}.mp3")
                with open(temp_raw, "wb") as f:
                    f.write(raw_data)

                # Transcode to Cloudflare-ready M4A
                cmd = [
                    FFMPEG_PATH or "ffmpeg", "-y", "-i", temp_raw,
                    "-map_metadata", "-1",
                    "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                    "-movflags", "+faststart",
                    "-metadata", f"title={clean_title}",
                    "-metadata", "artist=Audingo",
                    dst_m4a
                ]
                subprocess.run(cmd, capture_output=True)
                if os.path.exists(temp_raw):
                    os.remove(temp_raw)

                # Verify saved file
                if os.path.exists(dst_m4a) and os.path.getsize(dst_m4a) >= MIN_AUDIO_SIZE:
                    dur_out = ""
                    try:
                        dur_out = subprocess.check_output(
                            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', dst_m4a],
                            text=True
                        ).strip()
                    except Exception:
                        pass
                    sz_mb = os.path.getsize(dst_m4a) / (1024 * 1024)
                    print(f"        [V] SUCCESS! Saved: '{clean_title}.m4a' ({sz_mb:.2f} MB, Duration: {dur_out}s / Suno: {dur_str})")
                    total_downloaded += 1
                else:
                    print("        [!] Transcoding failed.")

                # Polite delay between versions (7-12s)
                v_delay = random.uniform(7.0, 12.0)
                print(f"        [*] Polite delay: {v_delay:.1f}s before next track...")
                time.sleep(v_delay)

            # Polite delay between songs (9-15s)
            s_delay = random.uniform(9.0, 15.0)
            print(f"     [*] Waiting {s_delay:.1f}s before next song...")
            time.sleep(s_delay)

        print("\n" + "=" * 80)
        print(f"   DOWNLOAD RUN COMPLETED! Downloaded: {total_downloaded}, Skipped (Healthy): {total_skipped}")
        print("=" * 80)

if __name__ == "__main__":
    run_downloader()
