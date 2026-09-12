"""
state_manager.py — Crash-safe, atomic JSON state management.

Schema of upload_state.json:
{
    "Ep_01": {
        "AR": "pending" | "loading" | "success" | "error",
        "EN": "pending",
        "ES": "pending",
        "PT": "pending"
    },
    "Ep_02": { ... }
}

The file is written atomically (temp → rename) so a crash during write
never leaves a corrupted JSON on disk.
"""

import json
import logging
import os
import tempfile
from pathlib import Path

from config import UPLOAD_STATE_FILE, UPLOAD_QUEUE_DIR, LANGUAGES

logger = logging.getLogger(__name__)

# Valid status values
STATUS_PENDING = "pending"
STATUS_LOADING = "loading"
STATUS_SUCCESS = "success"
STATUS_ERROR   = "error"

# Statuses that are eligible to be picked up and retried on the next run.
# ERROR is intentionally included: failed uploads are auto-retried rather
# than requiring a manual edit of upload_state.json.
RESUMABLE_STATUSES = {STATUS_PENDING, STATUS_LOADING, STATUS_ERROR}


# ─── Low-level I/O ────────────────────────────────────────────────────────────

def load_state() -> dict:
    """
    Load and return the full state dict.
    Returns an empty dict if the file does not yet exist.
    """
    if not UPLOAD_STATE_FILE.exists():
        logger.debug("upload_state.json not found — starting with empty state.")
        return {}
    try:
        with UPLOAD_STATE_FILE.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        logger.error("upload_state.json is corrupted (%s). Returning empty state.", exc)
        return {}


def save_state(state: dict) -> None:
    """
    Write *state* to disk atomically.

    Strategy: write to a sibling temp file, then os.replace() it over the
    real file. os.replace() is atomic on POSIX and near-atomic on Windows
    (within the same filesystem), preventing partial-write corruption.
    """
    parent = UPLOAD_STATE_FILE.parent
    parent.mkdir(parents=True, exist_ok=True)

    # Write to a temp file in the same directory
    fd, tmp_path = tempfile.mkstemp(dir=parent, suffix=".tmp", prefix="state_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, ensure_ascii=False, indent=2)
        os.replace(tmp_path, UPLOAD_STATE_FILE)
        logger.debug("upload_state.json saved successfully.")
    except Exception:
        # Clean up the temp file if something went wrong
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ─── High-level helpers ───────────────────────────────────────────────────────

def sync_state_with_queue(state: dict) -> dict:
    """
    Scan *Upload_Queue* for episode folders (Ep_XX pattern) and add any
    that are missing from *state* with all languages set to "pending".

    Episodes already present in *state* are left untouched (their existing
    statuses are preserved across crashes / re-runs).

    Returns the (possibly mutated) state dict.
    """
    if not UPLOAD_QUEUE_DIR.exists():
        logger.warning("Upload_Queue directory does not exist: %s", UPLOAD_QUEUE_DIR)
        return state

    episodes_on_disk = sorted(
        p.name for p in UPLOAD_QUEUE_DIR.iterdir()
        if p.is_dir() and p.name.startswith("Ep_")
    )

    added = []
    for ep in episodes_on_disk:
        if ep not in state:
            state[ep] = {lang: STATUS_PENDING for lang in LANGUAGES}
            added.append(ep)

    if added:
        logger.info("Added %d new episode(s) to state: %s", len(added), added)
        save_state(state)

    return state


def get_pending_uploads(state: dict) -> list[tuple[str, str]]:
    """
    Return a list of (episode, language) tuples whose status is
    "pending", "loading", OR "error" — all are considered resumable.
    Ordered by episode (alphabetical) then by the canonical LANGUAGES order.
    """
    pending = []
    for ep in sorted(state.keys()):
        for lang in LANGUAGES:
            if state[ep].get(lang) in RESUMABLE_STATUSES:
                pending.append((ep, lang))
    return pending


def set_upload_status(state: dict, episode: str, lang: str, status: str) -> dict:
    """
    Update the status for a single (episode, language) cell, persist to disk,
    and return the updated state.

    Args:
        state:   The current full state dict (mutated in-place).
        episode: e.g. "Ep_01"
        lang:    e.g. "AR"
        status:  One of the STATUS_* constants.
    """
    if episode not in state:
        state[episode] = {l: STATUS_PENDING for l in LANGUAGES}

    state[episode][lang] = status
    save_state(state)

    logger.info("[%s][%s] Status → %s", episode, lang, status.upper())
    return state


def is_episode_complete(state: dict, episode: str) -> bool:
    """Return True if every language for *episode* is "success"."""
    return all(
        state.get(episode, {}).get(lang) == STATUS_SUCCESS
        for lang in LANGUAGES
    )


def get_episode_summary(state: dict, episode: str) -> str:
    """Return a compact one-line summary of an episode's statuses."""
    parts = [f"{lang}={state.get(episode, {}).get(lang, '?')}" for lang in LANGUAGES]
    return f"[{episode}] " + " | ".join(parts)
