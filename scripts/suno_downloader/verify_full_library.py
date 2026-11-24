import os
import re
import json
import subprocess

BASE_DIR = r"C:\Users\ahmedMansour\Downloads\Suno-Audingo"
MANIFEST_PATH = os.path.join(BASE_DIR, "suno_library_manifest.json")

def verify_all():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        mf = json.load(f)

    total_checked = 0
    perfect_matches = 0
    missing = []
    truncated = []
    extended = []

    for s in mf["songs"]:
        fdir = os.path.join(BASE_DIR, s["folder"])
        local_files = [f for f in os.listdir(fdir) if f.endswith(".m4a") and not f.startswith("_temp")] if os.path.exists(fdir) else []
        
        vers = {}
        for lf in local_files:
            m = re.match(r'^(\d+(?:\.\d+)?)-?', lf)
            if m:
                p = os.path.join(fdir, lf)
                try:
                    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', p]
                    dur = float(subprocess.check_output(cmd, text=True).strip())
                    vers[m.group(1)] = (lf, dur)
                except Exception:
                    pass

        for v in s["versions"]:
            total_checked += 1
            v_token = v["version"]
            suno_dur = v["suno_duration_sec"]

            if v_token not in vers:
                missing.append((s["number"], s["name"], v["title"], suno_dur))
            else:
                fname, local_dur = vers[v_token]
                diff = suno_dur - local_dur
                if suno_dur > 0 and diff > 2.5: # short by >2.5s
                    truncated.append((s["number"], s["name"], fname, suno_dur, local_dur, diff))
                elif suno_dur > 0 and diff < -2.5: # long by >2.5s
                    extended.append((s["number"], s["name"], fname, suno_dur, local_dur, -diff))
                else:
                    perfect_matches += 1

    print("=" * 80)
    print("   COMPLETE DURATION VERIFICATION REPORT (ALL 517 SUNO TRACKS)")
    print("=" * 80)
    print(f"Total Tracks Checked   : {total_checked}")
    print(f"Perfect Matches (<=2s) : {perfect_matches}")
    print(f"Missing Tracks         : {len(missing)}")
    print(f"Truncated Tracks       : {len(truncated)}")
    print(f"Extended Tracks        : {len(extended)}")
    print("=" * 80)

    if missing:
        print("\nMISSING TRACKS:")
        for m in missing:
            print(" -", m)

    if truncated:
        print("\nTRUNCATED TRACKS:")
        for t in truncated:
            print(f" - #{t[0]} {t[2]}: Suno {t[3]}s vs Local {t[4]:.2f}s (Short by: {t[5]:.2f}s)")

    if extended:
        print("\nEXTENDED TRACKS:")
        for e in extended:
            print(f" - #{e[0]} {e[2]}: Suno {e[3]}s vs Local {e[4]:.2f}s (Long by: {e[5]:.2f}s)")

    return len(missing) == 0 and len(truncated) == 0 and len(extended) == 0

if __name__ == "__main__":
    verify_all()
