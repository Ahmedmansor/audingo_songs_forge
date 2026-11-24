"""
suno_rights_service.py — Service layer for tracking Suno monthly quota and commercial rights status.
Manages manifest loading, status persistence, metrics calculation, and reporting.
"""

import json
import os
import datetime
import functools
from typing import Dict, Any, List, Optional

PRIMARY_MANIFEST_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "scripts", "suno_downloader", "suno_library_manifest.json"
)
DOWNLOADS_MANIFEST_PATH = r"C:\Users\ahmedMansour\Downloads\Suno-Audingo\suno_library_manifest.json"

PRIMARY_STATUS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "scripts", "suno_downloader", "suno_rights_status.json"
)
DOWNLOADS_STATUS_PATH = r"C:\Users\ahmedMansour\Downloads\Suno-Audingo\suno_rights_status.json"

LOCAL_AUDIO_BASE = r"C:\Users\ahmedMansour\Downloads\Suno-Audingo"


@functools.lru_cache(maxsize=1)
def get_manifest_path() -> Optional[str]:
    for p in (PRIMARY_MANIFEST_PATH, DOWNLOADS_MANIFEST_PATH):
        if os.path.exists(p):
            return p
    return None


@functools.lru_cache(maxsize=1)
def load_manifest() -> Dict[str, Any]:
    path = get_manifest_path()
    if not path:
        return {"songs": [], "summary": {}, "total_songs": 0}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"songs": [], "summary": {}, "total_songs": 0}


def load_rights_status() -> Dict[str, Any]:
    for p in (PRIMARY_STATUS_PATH, DOWNLOADS_STATUS_PATH):
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                continue
    return {}


def save_rights_status(status: Dict[str, Any]) -> bool:
    success = False
    for p in (PRIMARY_STATUS_PATH, DOWNLOADS_STATUS_PATH):
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(status, f, indent=2, ensure_ascii=False)
            success = True
        except Exception:
            continue
    return success


def toggle_track_rights(track_title: str, secured: bool, notes: str = "") -> Dict[str, Any]:
    status = load_rights_status()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if secured:
        status[track_title] = {
            "secured": True,
            "updated_at": now_str,
            "notes": notes
        }
    else:
        if track_title in status:
            del status[track_title]
    save_rights_status(status)
    return status


def set_song_all_tracks(song: Dict[str, Any], secured: bool) -> Dict[str, Any]:
    status = load_rights_status()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for v in song.get("versions", []):
        title = v.get("title")
        if not title:
            continue
        if secured:
            status[title] = {
                "secured": True,
                "updated_at": now_str,
                "notes": ""
            }
        else:
            if title in status:
                del status[title]
    save_rights_status(status)
    return status


def get_audio_file_path(folder: Optional[str], local_file: Optional[str]) -> Optional[str]:
    if not folder or not local_file:
        return None
    try:
        candidate = os.path.join(LOCAL_AUDIO_BASE, str(folder), str(local_file))
        if os.path.exists(candidate):
            return candidate
    except Exception:
        return None
    return None


def calculate_metrics(manifest: Dict[str, Any], status: Dict[str, Any]) -> Dict[str, Any]:
    songs = manifest.get("songs", [])
    total_songs = len(songs)
    total_tracks = sum(len(s.get("versions", [])) for s in songs)

    secured_tracks = sum(1 for s in songs for v in s.get("versions", []) if status.get(v.get("title", ""), {}).get("secured"))
    pending_tracks = total_tracks - secured_tracks
    progress_pct = round((secured_tracks / total_tracks * 100), 1) if total_tracks > 0 else 0.0

    fully_secured_songs = 0
    partially_secured_songs = 0
    unsecured_songs = 0

    for s in songs:
        versions = s.get("versions", [])
        if not versions:
            continue
        s_count = sum(1 for v in versions if status.get(v.get("title", ""), {}).get("secured"))
        if s_count == len(versions):
            fully_secured_songs += 1
        elif s_count > 0:
            partially_secured_songs += 1
        else:
            unsecured_songs += 1

    return {
        "total_songs": total_songs,
        "total_tracks": total_tracks,
        "secured_tracks": secured_tracks,
        "pending_tracks": pending_tracks,
        "progress_pct": progress_pct,
        "fully_secured_songs": fully_secured_songs,
        "partially_secured_songs": partially_secured_songs,
        "unsecured_songs": unsecured_songs,
    }
