"""
draft_repository.py — Repository for Active Batch App State and Studio Drafts.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from data.database.connection import get_connection, DB_PATH


def save_active_batch_state(
    batch: List[Dict[str, Any]],
    concept: str = "",
    genre: str = "",
    song_structure: str = "",
    mood_analysis: Optional[Dict[str, Any]] = None,
    master_prompt: str = "",
    suno_prompt: str = "",
    poster_prompt: str = "",
    vocalist: str = "Male",
    selected_domain: str = "All Domains",
    db_path: Path = DB_PATH
) -> None:
    """Save active studio batch state to app_state table in SQLite."""
    payload = {
        "target_batch": batch,
        "custom_concept": concept,
        "selected_genre": genre,
        "selected_structure": song_structure,
        "mood_analysis": mood_analysis,
        "master_prompt": master_prompt,
        "suno_prompt": suno_prompt,
        "poster_prompt": poster_prompt,
        "selected_vocalist": vocalist,
        "selected_domain": selected_domain
    }
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO app_state (key, value) VALUES ('active_session', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (json.dumps(payload),)
        )
        conn.commit()


def load_active_batch_state(db_path: Path = DB_PATH) -> Dict[str, Any]:
    """Load active studio batch state from SQLite, returning empty dict if not found."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_state WHERE key = 'active_session'")
        row = cursor.fetchone()
        if row and row["value"]:
            try:
                return json.loads(row["value"])
            except Exception:
                return {}
    return {}


def clear_active_batch_state(db_path: Path = DB_PATH) -> None:
    """Clear active studio batch state from SQLite."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM app_state WHERE key = 'active_session'")
        conn.commit()


def save_studio_draft(
    song_title: str,
    batch: List[Dict[str, Any]],
    concept: str = "",
    genre: str = "",
    song_structure: str = "",
    mood_analysis: Optional[Dict[str, Any]] = None,
    master_prompt: str = "",
    suno_prompt: str = "",
    poster_prompt: str = "",
    vocalist: str = "Male",
    max_drafts: int = 10,
    db_path: Path = DB_PATH
) -> None:
    """Snapshot the current studio session as a named draft before approval."""
    word_names = [w["word"] for w in batch[:4]]
    label = ", ".join(word_names)
    if len(batch) > 4:
        label += f" +{len(batch) - 4} more"

    payload = {
        "target_batch": batch,
        "custom_concept": concept,
        "selected_genre": genre,
        "selected_structure": song_structure,
        "mood_analysis": mood_analysis,
        "master_prompt": master_prompt,
        "suno_prompt": suno_prompt,
        "poster_prompt": poster_prompt,
        "selected_vocalist": vocalist,
    }

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO studio_drafts (song_title, label, session_json)
            VALUES (?, ?, ?)
            """,
            (song_title.strip() or "Untitled", label, json.dumps(payload))
        )
        cursor.execute(
            """
            DELETE FROM studio_drafts
            WHERE id NOT IN (
                SELECT id FROM studio_drafts
                ORDER BY id DESC
                LIMIT ?
            )
            """,
            (max_drafts,)
        )
        conn.commit()


def list_studio_drafts(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Return all saved studio drafts, newest first."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, song_title, label, saved_at FROM studio_drafts ORDER BY id DESC"
        )
        rows = cursor.fetchall()
        return [
            {
                "id": r["id"],
                "song_title": r["song_title"],
                "label": r["label"],
                "saved_at": r["saved_at"],
            }
            for r in rows
        ]


def load_studio_draft(draft_id: int, db_path: Path = DB_PATH) -> Dict[str, Any]:
    """Load and return the full session payload for a specific draft by ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT session_json FROM studio_drafts WHERE id = ?",
            (draft_id,)
        )
        row = cursor.fetchone()
        if row and row["session_json"]:
            try:
                return json.loads(row["session_json"])
            except Exception:
                return {}
    return {}


def delete_studio_draft(draft_id: int, db_path: Path = DB_PATH) -> bool:
    """Delete a specific studio draft by ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM studio_drafts WHERE id = ?", (draft_id,))
        conn.commit()
        return cursor.rowcount > 0
