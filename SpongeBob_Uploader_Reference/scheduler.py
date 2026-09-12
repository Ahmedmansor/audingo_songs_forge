"""
scheduler.py — Egypt-timezone scheduling logic ("Two Trains" model).

Responsibilities:
  1. Compute the next available scheduled datetime for a given language
     using Two Trains logic: Train 1 (afternoon) and Train 2 (evening).
  2. Load / save schedule_tracker.json atomically.
  3. Increment the upload count after a confirmed successful schedule.

schedule_tracker.json schema:
{
    "2025-08-01": { "AR": 1, "EN": 2, "ES": 0, "PT": 1 },
    "2025-08-02": { "AR": 0, ... }
}

Keys are ISO-format dates (Egypt local date, UTC+2).

Two Trains algorithm (per language):
  For day = today, tomorrow, day+2, …:
    If day's upload count >= MAX  → skip day entirely.
    For train_slot in [Train1, Train2]:
      If train_slot datetime > now + 2 min  → return it.
  Raises RuntimeError if no slot found within 30 days (safety guard).
"""

import json
import logging
import os
import tempfile
from datetime import datetime, timedelta

import pytz

from config import (
    EGYPT_TIMEZONE,
    LANGUAGES,
    MAX_UPLOADS_PER_LANG_PER_DAY,
    PEAK_TIMES,
    SCHEDULE_TRACKER_FILE,
)

logger = logging.getLogger(__name__)

_tz = pytz.timezone(EGYPT_TIMEZONE)


# ─── Tracker I/O (atomic) ─────────────────────────────────────────────────────

def load_schedule_tracker() -> dict:
    """Load schedule_tracker.json. Returns {} if missing or corrupt."""
    if not SCHEDULE_TRACKER_FILE.exists():
        return {}
    try:
        with SCHEDULE_TRACKER_FILE.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        logger.error("schedule_tracker.json corrupted (%s) — starting fresh.", exc)
        return {}


def save_schedule_tracker(tracker: dict) -> None:
    """Write tracker atomically (temp → rename)."""
    parent = SCHEDULE_TRACKER_FILE.parent
    parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=parent, suffix=".tmp", prefix="sched_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(tracker, fh, ensure_ascii=False, indent=2)
        os.replace(tmp_path, SCHEDULE_TRACKER_FILE)
        logger.debug("schedule_tracker.json saved.")
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ─── Core scheduling logic ────────────────────────────────────────────────────

def _build_candidate(date: "datetime.date", slot: dict) -> datetime:
    """
    Build a timezone-aware datetime from a calendar date and a slot dict
    (e.g. {"hour": 14, "minute": 0}).
    """
    naive = datetime(date.year, date.month, date.day, slot["hour"], slot["minute"], 0)
    return _tz.localize(naive)


_last_assigned_train: dict[str, int] = {}


def get_next_slot(lang: str) -> tuple[datetime, str]:
    """
    Two Trains algorithm: find the next available upload slot for *lang*.

    For each calendar day starting from today, the function checks Train 1
    then Train 2.  A slot is eligible when:
      - Its datetime is more than 2 minutes in the future, AND
      - We haven't already consumed that train or a later one today.

    Returns:
        (scheduled_datetime, date_key)  where date_key is "YYYY-MM-DD".
    Raises:
        RuntimeError if no slot is found within 30 days (safety guard).
    """
    tracker = load_schedule_tracker()
    now = datetime.now(_tz)
    today = now.date()
    trains = PEAK_TIMES[lang]   # list of two slot dicts: [Train1, Train2]

    for day_offset in range(31):           # safety guard: max 30 days ahead
        candidate_date = today + timedelta(days=day_offset)
        date_key = candidate_date.isoformat()
        
        # day_count now tracks the highest train_num (1-based) already consumed today
        day_count = tracker.get(date_key, {}).get(lang, 0)

        if day_count >= MAX_UPLOADS_PER_LANG_PER_DAY:
            logger.debug(
                "[%s] %s is fully booked (%d/%d) — skipping to next day.",
                lang, date_key, day_count, MAX_UPLOADS_PER_LANG_PER_DAY,
            )
            continue

        # Check Train 1, then Train 2
        for train_num, slot in enumerate(trains, start=1):
            if train_num <= day_count:
                continue  # we already used this train or a later one!
                
            candidate_dt = _build_candidate(candidate_date, slot)
            if candidate_dt > now + timedelta(minutes=2):
                logger.info(
                    "[%s] Next slot → Train %d on %s at %s  (trains consumed today: %d/%d)",
                    lang, train_num, date_key,
                    candidate_dt.strftime("%H:%M %Z"),
                    day_count, MAX_UPLOADS_PER_LANG_PER_DAY,
                )
                _last_assigned_train[lang] = train_num
                return candidate_dt, date_key

    raise RuntimeError(
        f"[{lang}] No available upload slot found within the next 30 days. "
        "Check schedule_tracker.json for anomalies."
    )


def increment_upload_count(lang: str, date_key: str) -> None:
    """
    Increment the upload counter for *lang* on *date_key* in the tracker.
    Must be called only after a confirmed successful schedule action.
    """
    tracker = load_schedule_tracker()
    if date_key not in tracker:
        tracker[date_key] = {l: 0 for l in LANGUAGES}
    tracker[date_key].setdefault(lang, 0)
    
    assigned_train = _last_assigned_train.get(lang)
    if assigned_train is not None:
        tracker[date_key][lang] = assigned_train
    else:
        # Fallback to simple increment if state is lost
        tracker[date_key][lang] += 1
        
    save_schedule_tracker(tracker)
    
    consumed_display = assigned_train if assigned_train is not None else tracker[date_key][lang]
    logger.info(
        "[%s] Tracked train %d for %s (total consumed today: %d).",
        lang, consumed_display, date_key, tracker[date_key][lang],
    )


def get_daily_counts(date_key: str | None = None) -> dict:
    """
    Return the upload counts for a given date (defaults to today — Egypt TZ).
    Useful for --dry-run display and pre-flight checks.
    """
    if date_key is None:
        date_key = datetime.now(_tz).date().isoformat()
    tracker = load_schedule_tracker()
    return tracker.get(date_key, {lang: 0 for lang in LANGUAGES})


def format_scheduled_time_for_yt(dt: datetime) -> tuple[str, str]:
    """
    Convert a datetime to the date and time strings expected by the
    YouTube Studio scheduling UI.

    Returns:
        (date_str, time_str)  e.g. ("08/15/2025", "07:00 PM")
    """
    date_str = dt.strftime("%m/%d/%Y")   # MM/DD/YYYY
    time_str = dt.strftime("%I:%M %p")   # hh:MM AM/PM  (e.g. "07:00 PM")
    return date_str, time_str
