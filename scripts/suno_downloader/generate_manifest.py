import os
import re
import json
import time
import subprocess
from playwright.sync_api import sync_playwright

BASE_DIR = r"C:\Users\ahmedMansour\Downloads\Suno-Audingo"
SONGS_JSON = os.path.join(BASE_DIR, "songs.json")
OUTPUT_MANIFEST = os.path.join(BASE_DIR, "suno_library_manifest.json")

def get_local_audio_info(folder_path):
    """Maps version token -> { filename, duration_sec, size_bytes }"""
    if not os.path.exists(folder_path):
        return {}
    res = {}
    for fname in os.listdir(folder_path):
        if not fname.endswith(".m4a") and not fname.endswith(".mp3"):
            continue
        if fname.startswith("_temp"):
            continue
        fpath = os.path.join(folder_path, fname)
        m = re.match(r'^(\d+(?:\.\d+)?)-?', fname)
        if not m:
            continue
        ver = m.group(1)

        # Get exact duration via ffprobe
        dur = 0.0
        try:
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', fpath]
            out = subprocess.check_output(cmd, text=True).strip()
            dur = float(out)
        except Exception:
            pass

        res[ver] = {
            "filename": fname,
            "filepath": fpath,
            "size_bytes": os.path.getsize(fpath),
            "local_duration_sec": round(dur, 2)
        }
    return res

def parse_duration_text(text):
    """Parses mm:ss or m:ss into total integer seconds."""
    m = re.search(r'\b(\d+):([0-5]\d)\b', text)
    if m:
        mins = int(m.group(1))
        secs = int(m.group(2))
        return mins * 60 + secs, f"{mins}:{secs:02d}"
    return 0, ""

def scan_all_to_manifest():
    if not os.path.exists(SONGS_JSON):
        print(f"[!] {SONGS_JSON} not found!")
        return

    with open(SONGS_JSON, "r", encoding="utf-8") as f:
        songs = json.load(f)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = next((pg for pg in context.pages if "suno.com" in pg.url and "create" in pg.url), None)
        if not page:
            print("[X] Suno create tab not found!")
            return

        search_input = page.locator('input[placeholder*="Search" i], input[type="search" i]').first

        full_manifest = {
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_songs": len(songs),
            "summary": {
                "total_suno_tracks": 0,
                "fully_downloaded_exact": 0,
                "missing_tracks": 0,
                "truncated_tracks": 0
            },
            "songs": []
        }

        print("=" * 80)
        print("   Suno Library Deep Scan: Building Duration Manifest (All 133 Songs)")
        print("=" * 80)

        for idx, song in enumerate(songs, 1):
            num = str(song.get("number")).strip()
            name = song.get("name", "").strip()
            folder_num = int(num) if num.isdigit() else num
            folder_name = f"{folder_num:02d}- {name}" if isinstance(folder_num, int) else f"{folder_num}- {name}"
            folder_path = os.path.join(BASE_DIR, folder_name)
            if not os.path.exists(folder_path):
                folder_path = os.path.join(BASE_DIR, f"{folder_num}- {name}")

            local_files = get_local_audio_info(folder_path)

            # Search on Suno: First by name
            search_input.fill("")
            search_input.type(name, delay=15)
            search_input.press("Enter")
            time.sleep(1.6)

            # Scroll twice
            page.mouse.wheel(0, 1500)
            time.sleep(0.3)
            page.mouse.wheel(0, 1500)
            time.sleep(0.3)

            # Extract clips: aria-label, text, and row data
            clips_raw = page.evaluate("""(targetNum) => {
                const found = [];
                const regex = new RegExp('^' + targetNum + '(\\\\.\\\\d+)?-?\\\\s*(.+)', 'i');
                const rows = document.querySelectorAll('[data-testid="clip-row"]');
                for (let r of rows) {
                    const aria = (r.getAttribute('aria-label') || '').trim();
                    const txt = r.innerText || '';
                    const m = regex.exec(aria);
                    if (m) {
                        found.push({
                            aria: aria,
                            text: txt
                        });
                    }
                }
                return found;
            }""", num)

            # If none found or special numbers (3, 13, 14, 131, 133), also try searching by number
            if len(clips_raw) == 0 or num in ["3", "13", "14", "131", "133"]:
                search_input.fill("")
                search_input.type(f"{num}-", delay=15)
                search_input.press("Enter")
                time.sleep(1.5)
                more_raw = page.evaluate("""(targetNum) => {
                    const found = [];
                    const regex = new RegExp('^' + targetNum + '(\\\\.\\\\d+)?-?\\\\s*(.+)', 'i');
                    const rows = document.querySelectorAll('[data-testid="clip-row"]');
                    for (let r of rows) {
                        const aria = (r.getAttribute('aria-label') || '').trim();
                        const txt = r.innerText || '';
                        const m = regex.exec(aria);
                        if (m) {
                            found.push({
                                aria: aria,
                                text: txt
                            });
                        }
                    }
                    return found;
                }""", num)
                existing_arias = {c["aria"] for c in clips_raw}
                for c in more_raw:
                    if c["aria"] not in existing_arias:
                        clips_raw.append(c)

            # For 13 and 14 if empty, check without hyphen (e.g. "13 " or "14 ")
            if len(clips_raw) == 0 and num in ["13", "14"]:
                search_input.fill("")
                search_input.type(f"{num} ", delay=15)
                search_input.press("Enter")
                time.sleep(1.5)
                more_raw = page.evaluate("""(targetNum) => {
                    const found = [];
                    const regex = new RegExp('^' + targetNum + '\\\\s*(.+)', 'i');
                    const rows = document.querySelectorAll('[data-testid="clip-row"]');
                    for (let r of rows) {
                        const aria = (r.getAttribute('aria-label') || '').trim();
                        const txt = r.innerText || '';
                        const m = regex.exec(aria);
                        if (m) found.push({ aria: aria, text: txt });
                    }
                    return found;
                }""", num)
                existing_arias = {c["aria"] for c in clips_raw}
                for c in more_raw:
                    if c["aria"] not in existing_arias:
                        clips_raw.append(c)

            # Process clips for this song
            song_entry = {
                "number": num,
                "name": name,
                "folder": os.path.basename(folder_path),
                "versions": []
            }

            seen_versions = set()
            for c in clips_raw:
                full_title = c["aria"]
                m_ver = re.match(r'^(\d+(?:\.\d+)?)-?', full_title)
                ver_token = m_ver.group(1) if m_ver else num
                if ver_token in seen_versions:
                    continue
                seen_versions.add(ver_token)

                suno_sec, dur_str = parse_duration_text(c["text"])
                loc = local_files.get(ver_token)

                loc_sec = loc["local_duration_sec"] if loc else 0.0
                loc_file = loc["filename"] if loc else None
                diff = round(suno_sec - loc_sec, 2) if loc else suno_sec
                # Truncated if local duration is more than 3 seconds shorter than Suno
                is_trunc = (loc is not None) and (diff > 3.0)
                is_missing = (loc is None)

                ver_obj = {
                    "version": ver_token,
                    "title": full_title,
                    "suno_duration_str": dur_str,
                    "suno_duration_sec": suno_sec,
                    "local_file": loc_file,
                    "local_duration_sec": loc_sec,
                    "duration_diff_sec": diff,
                    "status": "MISSING" if is_missing else ("TRUNCATED" if is_trunc else "COMPLETE")
                }
                song_entry["versions"].append(ver_obj)

                full_manifest["summary"]["total_suno_tracks"] += 1
                if is_missing:
                    full_manifest["summary"]["missing_tracks"] += 1
                elif is_trunc:
                    full_manifest["summary"]["truncated_tracks"] += 1
                else:
                    full_manifest["summary"]["fully_downloaded_exact"] += 1

            full_manifest["songs"].append(song_entry)

            # Console status
            missing_cnt = sum(1 for v in song_entry["versions"] if v["status"] == "MISSING")
            trunc_cnt = sum(1 for v in song_entry["versions"] if v["status"] == "TRUNCATED")
            ok_cnt = sum(1 for v in song_entry["versions"] if v["status"] == "COMPLETE")

            status_str = f"OK: {ok_cnt}"
            if missing_cnt > 0:
                status_str += f", MISSING: {missing_cnt}"
            if trunc_cnt > 0:
                status_str += f", TRUNCATED: {trunc_cnt}"

            print(f"[{idx:3d}/133] #{num} '{name}': {len(song_entry['versions'])} Suno version(s) ({status_str})")
            if trunc_cnt > 0:
                for v in song_entry["versions"]:
                    if v["status"] == "TRUNCATED":
                        print(f"      [!] TRUNCATED: {v['version']} -> Suno: {v['suno_duration_str']} ({v['suno_duration_sec']}s) vs Local: {v['local_duration_sec']}s (short by {v['duration_diff_sec']}s)")

        # Save manifest
        with open(OUTPUT_MANIFEST, "w", encoding="utf-8") as f:
            json.dump(full_manifest, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 80)
        print("   MANIFEST COMPLETED & SAVED TO suno_library_manifest.json")
        print("=" * 80)
        print(f"Total Suno Tracks Found : {full_manifest['summary']['total_suno_tracks']}")
        print(f"Fully Complete & Match   : {full_manifest['summary']['fully_downloaded_exact']}")
        print(f"Missing (Not Downloaded) : {full_manifest['summary']['missing_tracks']}")
        print(f"Truncated (Short/Cutoff) : {full_manifest['summary']['truncated_tracks']}")
        print("=" * 80)

if __name__ == "__main__":
    scan_all_to_manifest()
