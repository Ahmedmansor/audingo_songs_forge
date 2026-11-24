import os
import re
import sys
import shutil
import subprocess

SUNO_DIR = os.path.dirname(os.path.abspath(__file__))
FFMPEG_PATH = shutil.which("ffmpeg")
if not FFMPEG_PATH:
    winget_ffmpeg = r"C:\Users\ahmedMansour\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"
    if os.path.exists(winget_ffmpeg):
        FFMPEG_PATH = winget_ffmpeg

AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".aac", ".ogg", ".flac"}

def clean_title_str(text):
    return re.sub(r'[\s\-_\.,\(\)\'\"]+', ' ', text).strip().lower()

def get_existing_folders():
    folders = {}
    for entry in os.listdir(SUNO_DIR):
        folder_path = os.path.join(SUNO_DIR, entry)
        if os.path.isdir(folder_path):
            m = re.match(r'^(\d+)[\s\-_]+(.*)', entry)
            if m:
                num = int(m.group(1))
                clean_title = clean_title_str(m.group(2))
                folders[entry] = {
                    "num": num,
                    "title": clean_title,
                    "raw": entry
                }
    return folders

def find_matching_folder(filename, existing_folders):
    name_no_ext = os.path.splitext(filename)[0]
    
    # 1. Match by leading song number (e.g. 50-, 50_, 50 .)
    m = re.match(r'^(\d+)[\s\-_]+(.*)', name_no_ext)
    if m:
        num = int(m.group(1))
        for folder_name, data in existing_folders.items():
            if data["num"] == num:
                return folder_name
    
    # 2. Match by full song title (must be at least 4 characters to avoid false matches)
    cleaned_filename = clean_title_str(name_no_ext)
    for folder_name, data in existing_folders.items():
        title = data["title"]
        if len(title) >= 4 and title in cleaned_filename:
            return folder_name

    # 3. If file starts with a number, create a new song folder
    if m:
        num = int(m.group(1))
        title = m.group(2).strip().strip('-').strip()
        new_folder = f"{num:02d}- {title}"
        return new_folder

    return None

def convert_to_m4a(src_file, dst_file):
    if not FFMPEG_PATH:
        print(f"[!] FFmpeg not found. Cannot convert {src_file}")
        return False
    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i", src_file,
        "-c:a", "aac",
        "-b:a", "256k",
        dst_file
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if res.returncode == 0 and os.path.exists(dst_file) and os.path.getsize(dst_file) > 10000:
        return True
    return False

def organize():
    print("=" * 60)
    print("      Suno-Audingo Songs & Styles Auto-Organizer")
    print("=" * 60)
    
    existing_folders = get_existing_folders()
    print(f"[*] Found {len(existing_folders)} song folders in Suno-Audingo.")

    # Find all loose audio files in SUNO_DIR root
    loose_files = [
        f for f in os.listdir(SUNO_DIR)
        if os.path.isfile(os.path.join(SUNO_DIR, f))
        and os.path.splitext(f)[1].lower() in AUDIO_EXTS
        and not f.endswith(".py")
        and not f.endswith(".bat")
    ]

    if not loose_files:
        print("[i] No loose audio files found in Suno-Audingo root directory.")
        print("[i] Everything is already neatly organized in its folders!")
        return

    print(f"[*] Processing {len(loose_files)} loose audio file(s)...")

    for filename in loose_files:
        src_path = os.path.join(SUNO_DIR, filename)
        target_folder_name = find_matching_folder(filename, existing_folders)
        
        if not target_folder_name:
            print(f"[-] Could not match to a song folder: {filename}")
            continue

        target_folder_path = os.path.join(SUNO_DIR, target_folder_name)
        os.makedirs(target_folder_path, exist_ok=True)
        
        # Keep folder index updated
        if target_folder_name not in existing_folders:
            m = re.match(r'^(\d+)[\s\-_]+(.*)', target_folder_name)
            if m:
                existing_folders[target_folder_name] = {
                    "num": int(m.group(1)),
                    "title": clean_title_str(m.group(2)),
                    "raw": target_folder_name
                }

        name_part, ext_part = os.path.splitext(filename)
        clean_name_part = re.sub(r'[\-]+$', '', name_part).strip()

        if ext_part.lower() == ".m4a":
            dst_file = os.path.join(target_folder_path, f"{clean_name_part}.m4a")
            if os.path.exists(dst_file) and os.path.abspath(src_path) != os.path.abspath(dst_file):
                idx = 2
                while os.path.exists(os.path.join(target_folder_path, f"{clean_name_part} (Style {idx}).m4a")):
                    idx += 1
                dst_file = os.path.join(target_folder_path, f"{clean_name_part} (Style {idx}).m4a")

            if os.path.abspath(src_path) != os.path.abspath(dst_file):
                shutil.move(src_path, dst_file)
                print(f"[+] Moved: {filename} -> {target_folder_name}/{os.path.basename(dst_file)}")
        else:
            # Convert to m4a
            dst_file = os.path.join(target_folder_path, f"{clean_name_part}.m4a")
            if os.path.exists(dst_file):
                idx = 2
                while os.path.exists(os.path.join(target_folder_path, f"{clean_name_part} (Style {idx}).m4a")):
                    idx += 1
                dst_file = os.path.join(target_folder_path, f"{clean_name_part} (Style {idx}).m4a")

            print(f"[*] Converting & Moving: {filename} -> {target_folder_name}/{os.path.basename(dst_file)}...")
            if convert_to_m4a(src_path, dst_file):
                os.remove(src_path)
                print(f"[+] Converted successfully & removed source: {filename}")
            else:
                print(f"[!] Failed to convert {filename}")

    print("\n[V] Organization complete!")

if __name__ == "__main__":
    organize()
