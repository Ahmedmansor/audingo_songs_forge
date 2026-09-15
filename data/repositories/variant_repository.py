"""
variant_repository.py — Repository for Track Variants (Suno prompts) and Poster Prompts.
"""

import sqlite3
from pathlib import Path
from typing import List, Optional
from data.database.connection import get_connection, DB_PATH


def upsert_track_variant(
    song_id: int,
    genre: str,
    vocalist: str,
    suno_prompt: str,
    poster_prompt: str,
    db_path: Path = DB_PATH
) -> int:
    """Insert or update a track variant (Suno music prompt + poster prompt)."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO track_variants (song_id, genre, vocalist, suno_prompt, poster_prompt, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(song_id, genre, vocalist) DO UPDATE SET
                suno_prompt = excluded.suno_prompt,
                poster_prompt = excluded.poster_prompt,
                created_at = CURRENT_TIMESTAMP
            """,
            (song_id, genre.strip(), vocalist.strip(), suno_prompt.strip(), poster_prompt.strip())
        )
        conn.commit()
        cursor.execute(
            "SELECT id FROM track_variants WHERE song_id = ? AND genre = ? AND vocalist = ?",
            (song_id, genre.strip(), vocalist.strip())
        )
        row = cursor.fetchone()
        return row["id"] if row else cursor.lastrowid


save_track_variant = upsert_track_variant


def get_track_variants(song_id: int, db_path: Path = DB_PATH) -> List[sqlite3.Row]:
    """Retrieve all track variants for a song, ordered latest first."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, song_id, genre, vocalist, suno_prompt, poster_prompt, created_at FROM track_variants WHERE song_id = ? ORDER BY id DESC",
            (song_id,)
        )
        return cursor.fetchall()


def get_track_variant_by_combo(
    song_id: int,
    genre: str,
    vocalist: str,
    db_path: Path = DB_PATH
) -> Optional[sqlite3.Row]:
    """Retrieve a specific track variant by (song_id, genre, vocalist) combo if it exists."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, song_id, genre, vocalist, suno_prompt, poster_prompt, created_at FROM track_variants WHERE song_id = ? AND genre = ? AND vocalist = ?",
            (song_id, genre.strip(), vocalist.strip())
        )
        return cursor.fetchone()


def update_track_variant(
    variant_id: int,
    suno_prompt: str,
    poster_prompt: str,
    db_path: Path = DB_PATH
) -> bool:
    """Update both Suno prompt and poster prompt for a variant."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE track_variants SET suno_prompt = ?, poster_prompt = ? WHERE id = ?",
            (suno_prompt.strip(), poster_prompt.strip(), variant_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_track_variant(variant_id: int, db_path: Path = DB_PATH) -> bool:
    """Delete a track variant by ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM track_variants WHERE id = ?", (variant_id,))
        conn.commit()
        return cursor.rowcount > 0


def upsert_poster_prompt(
    song_id: int,
    genre: str,
    vocalist: str,
    prompt_text: str,
    db_path: Path = DB_PATH
) -> int:
    """Insert or update a poster prompt for a (song_id, genre, vocalist) combination."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO poster_prompts (song_id, genre, vocalist, prompt_text, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(song_id, genre, vocalist) DO UPDATE SET
                prompt_text = excluded.prompt_text,
                created_at = CURRENT_TIMESTAMP
            """,
            (song_id, genre.strip(), vocalist.strip(), prompt_text.strip())
        )
        conn.commit()
        cursor.execute(
            "SELECT id FROM poster_prompts WHERE song_id = ? AND genre = ? AND vocalist = ?",
            (song_id, genre.strip(), vocalist.strip())
        )
        row = cursor.fetchone()
        return row["id"] if row else cursor.lastrowid


def get_poster_prompts(song_id: int, db_path: Path = DB_PATH) -> List[sqlite3.Row]:
    """Retrieve all poster prompts saved for a specific song, ordered by latest first."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, song_id, genre, vocalist, prompt_text, created_at FROM poster_prompts WHERE song_id = ? ORDER BY id DESC",
            (song_id,)
        )
        return cursor.fetchall()


def update_poster_prompt(prompt_id: int, new_text: str, db_path: Path = DB_PATH) -> bool:
    """Update the text of an existing poster prompt."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE poster_prompts SET prompt_text = ? WHERE id = ?",
            (new_text.strip(), prompt_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_poster_prompt(prompt_id: int, db_path: Path = DB_PATH) -> bool:
    """Delete a poster prompt by its ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM poster_prompts WHERE id = ?", (prompt_id,))
        conn.commit()
        return cursor.rowcount > 0
