"""Associate a critic report with the exact lyric version it evaluated."""

from copy import deepcopy
from datetime import datetime, timezone
import json
import re
from typing import Any, Mapping, Optional


def lyrics_signature(text: str) -> tuple[str, ...]:
    """Ignore layout/section labels, but preserve wording, order and repetitions."""
    lines = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if lower.startswith(("[words used]", "[words left out]")):
            break
        if lower.startswith(("[title]:", "[genre]:", "[suno style]:")):
            continue
        if not stripped or re.fullmatch(r"\[[^\]]+\]:?", stripped):
            continue
        stripped = stripped.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'}))
        lines.append(" ".join(stripped.split()))
    return tuple(lines)


def report_matches_lyrics(snapshot: Mapping[str, Any], lyrics: str) -> bool:
    evaluated = lyrics_signature(snapshot.get("evaluated_lyrics", ""))
    return bool(evaluated) and evaluated == lyrics_signature(lyrics)


def report_applies_to_draft(report: Any, draft: str) -> bool:
    """A pipeline report belongs to its input draft as well as its final output."""
    signature = lyrics_signature(draft)
    if not signature or not isinstance(report, dict):
        return False
    return any(
        signature == lyrics_signature(report.get(key, ""))
        for key in ("raw_lyrics", "input_lyrics", "final_lyrics")
    )


def select_refinement_snapshot(
    lyrics: str, session: Mapping[str, Any], persisted: Mapping[str, Any]
) -> tuple[Optional[dict], bool]:
    """Prefer the selected mode, then any matching report. Never attach a stale one."""
    critic_mode = session.get("critic_only_mode", persisted.get("critic_only_mode", True))
    modes = ["critic_only", "pipeline"] if critic_mode else ["pipeline", "critic_only"]
    has_report = False
    for mode in modes:
        key = "critic_only_report" if mode == "critic_only" else "graph_report"
        report = session[key] if key in session else persisted.get(key)
        if not isinstance(report, dict) or not report.get("line_breakdown"):
            continue
        has_report = True
        snapshot = {
            "schema_version": 1,
            "mode": mode,
            "archived_at": datetime.now(timezone.utc).isoformat(),
            "evaluated_lyrics": report.get("raw_lyrics" if mode == "critic_only" else "final_lyrics", ""),
            "report": deepcopy(report),
        }
        if report_matches_lyrics(snapshot, lyrics):
            return snapshot, False
    return None, has_report


def parse_refinement_snapshot(raw: Any) -> Optional[dict]:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (ValueError, TypeError):
            return None
    if not isinstance(raw, dict) or not isinstance(raw.get("report"), dict):
        return None
    return raw
