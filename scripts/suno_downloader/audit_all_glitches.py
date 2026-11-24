import os
import subprocess
import struct
import math
import json

BASE_DIR = r"C:\Users\ahmedMansour\Downloads\Suno-Audingo"
FFMPEG_PATH = r"C:\Users\ahmedMansour\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"

def audit_file(fpath):
    # Stage 1: Demuxing & frame integrity
    cmd1 = [FFMPEG_PATH, '-v', 'error', '-i', fpath, '-f', 'null', '-']
    res1 = subprocess.run(cmd1, capture_output=True, text=True)
    if res1.returncode != 0 or res1.stderr.strip():
        return False, f"FFMPEG_ERROR: {res1.stderr.strip()[:100]}"

    # Stage 2: Signal analysis for audio screech/glitch/clipping
    cmd2 = [FFMPEG_PATH, '-y', '-i', fpath, '-f', 's16le', '-ac', '1', '-ar', '16000', '-']
    proc = subprocess.Popen(cmd2, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    raw, _ = proc.communicate()
    if not raw or len(raw) < 16000:
        return False, "EMPTY_AUDIO"

    samples = struct.unpack(f'<{len(raw)//2}h', raw)
    sr = 16000
    total_sec = len(samples) // sr

    severe_glitch_secs = []
    for s in range(0, total_sec):
        chunk = samples[s*sr : (s+1)*sr]
        if len(chunk) < sr:
            break
        hf = sum(abs(chunk[i] - chunk[i-1]) for i in range(1, len(chunk)))
        vol = sum(abs(x) for x in chunk) + 1
        ratio = hf / vol
        clipped = sum(1 for x in chunk if abs(x) > 32600)

        # Severe noise glitch threshold: >500 clipped samples per sec + high frequency energy
        if clipped > 500 and ratio > 0.45:
            severe_glitch_secs.append(s)

    if len(severe_glitch_secs) >= 3:
        return False, f"GLITCH_DETECTED: {len(severe_glitch_secs)} noisy seconds at {severe_glitch_secs[:5]}"

    return True, "PRISTINE"

def audit_entire_library():
    print("=" * 80)
    print("   STARTING TWO-STAGE NOISE & GLITCH AUDIT (ALL FILES)")
    print("=" * 80)

    total_audited = 0
    clean_count = 0
    bad_files = []

    for folder in sorted(os.listdir(BASE_DIR)):
        fpath = os.path.join(BASE_DIR, folder)
        if not os.path.isdir(fpath) or folder.startswith('_') or folder == 'test_single':
            continue

        files = [f for f in os.listdir(fpath) if f.endswith('.m4a') and not f.startswith('_temp')]
        for f in sorted(files):
            total_audited += 1
            audio_path = os.path.join(fpath, f)
            ok, msg = audit_file(audio_path)
            if ok:
                clean_count += 1
            else:
                bad_files.append((folder, f, msg))
                print(f"[!] DEFECT FOUND: {folder} / {f} -> {msg}")

            if total_audited % 50 == 0:
                print(f"Audited {total_audited} files... ({clean_count} pristine, {len(bad_files)} flagged)")

    print("=" * 80)
    print("   FINAL QUALITY AUDIT SUMMARY")
    print("=" * 80)
    print(f"Total Audio Files Audited : {total_audited}")
    print(f"Pristine & Clean Files   : {clean_count}")
    print(f"Flagged / Glitched Files  : {len(bad_files)}")
    print("=" * 80)

    with open(os.path.join(BASE_DIR, "glitch_audit_results.json"), "w", encoding="utf-8") as f:
        json.dump({"total": total_audited, "clean": clean_count, "bad": bad_files}, f, indent=2)

if __name__ == "__main__":
    audit_entire_library()
