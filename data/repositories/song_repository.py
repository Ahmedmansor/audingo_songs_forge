"""
song_repository.py — Repository for songs approval, listing, updating, deletion, and rollback.
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set
import pandas as pd
from data.database.connection import get_connection, get_cairo_now_str, DB_PATH


def approve_and_save_song(
    title: str,
    lyrics: str,
    target_words: List[str],
    checked_bonus_words: List[str],
    checked_extra_words: List[str],
    checked_target_words: Optional[List[str]] = None,
    reused_words: Optional[List[str]] = None,
    mood_breakdown: Optional[Dict[str, Any]] = None,
    genre: str = "",
    song_structure: str = "",
    creative_concept: str = "",
    db_path: Path = DB_PATH
) -> Tuple[int, int, int]:
    """Approve and save song atomically, incrementing usage for words."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        actual_target_words = checked_target_words if checked_target_words is not None else target_words
        target_words_str = ", ".join(actual_target_words)
        bonus_words_str = ", ".join(checked_bonus_words)
        reused_words_str = ", ".join(reused_words or [])
        extra_words_str = ", ".join(checked_extra_words)
        mood_json = json.dumps(mood_breakdown) if isinstance(mood_breakdown, dict) else (mood_breakdown or "")

        cairo_now = get_cairo_now_str()
        cursor.execute(
            """
            INSERT INTO songs (
                title, lyrics, target_words, bonus_words, reused_words, extra_words,
                mood_breakdown, genre, song_structure, creative_concept, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title, lyrics, target_words_str, bonus_words_str, reused_words_str, extra_words_str,
                mood_json, genre, song_structure, creative_concept, cairo_now
            )
        )
        song_id = cursor.lastrowid
        
        all_ngsl_to_increment = actual_target_words + checked_bonus_words + (reused_words or [])
        unique_ngsl = list(set([w.lower().strip() for w in all_ngsl_to_increment if w.strip()]))
        if unique_ngsl:
            placeholders = ",".join("?" * len(unique_ngsl))
            cursor.execute(
                f"UPDATE ngsl_words SET usage_count = usage_count + 1 WHERE LOWER(word) IN ({placeholders})",
                unique_ngsl
            )
            
        unique_extra = list(set([w.lower().strip() for w in checked_extra_words if w.strip()]))
        for extra in unique_extra:
            cursor.execute(
                """
                INSERT INTO extra_words (word, occurrence_count, first_seen_in_song)
                VALUES (?, 1, ?)
                ON CONFLICT(word) DO UPDATE SET occurrence_count = occurrence_count + 1
                """,
                (extra, title)
            )
            
        conn.commit()
        return song_id, len(unique_ngsl), len(unique_extra)


def get_all_songs(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Retrieve all saved songs from the database, sorted newest first."""
    with get_connection(db_path) as conn:
        df = pd.read_sql_query(
            "SELECT id, title, lyrics, target_words, bonus_words, reused_words, extra_words, mood_breakdown, genre, song_structure, creative_concept, created_at FROM songs ORDER BY id DESC",
            conn
        )
        return df


def update_song(
    song_id: int,
    title: str,
    lyrics: str,
    target_words: str,
    bonus_words: Optional[str] = None,
    reused_words: Optional[str] = None,
    extra_words: Optional[str] = None,
    mood_breakdown: Optional[Dict[str, Any]] = None,
    genre: Optional[str] = None,
    song_structure: Optional[str] = None,
    creative_concept: Optional[str] = None,
    sync_ngsl_usage: bool = True,
    db_path: Path = DB_PATH
) -> bool:
    """Update an existing song's details and metadata in SQLite."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT target_words, bonus_words, extra_words, title FROM songs WHERE id = ?", (song_id,))
        row = cursor.fetchone()
        if not row:
            return False
            
        old_targets = set(w.strip().lower() for w in (row["target_words"] or "").split(",") if w.strip())
        new_targets_list = [w.strip() for w in target_words.split(",") if w.strip()]
        new_targets_set = set(w.lower() for w in new_targets_list)
        
        updates = [
            ("title", title),
            ("lyrics", lyrics),
            ("target_words", ", ".join(new_targets_list))
        ]
        if bonus_words is not None:
            new_bonuses = [w.strip() for w in bonus_words.split(",") if w.strip()]
            updates.append(("bonus_words", ", ".join(new_bonuses)))
        if reused_words is not None:
            new_reused = [w.strip() for w in reused_words.split(",") if w.strip()]
            updates.append(("reused_words", ", ".join(new_reused)))
        if extra_words is not None:
            new_extras = [w.strip() for w in extra_words.split(",") if w.strip()]
            updates.append(("extra_words", ", ".join(new_extras)))
        if mood_breakdown is not None:
            mood_val = json.dumps(mood_breakdown) if isinstance(mood_breakdown, dict) else str(mood_breakdown)
            updates.append(("mood_breakdown", mood_val))
        if genre is not None:
            updates.append(("genre", genre))
        if song_structure is not None:
            updates.append(("song_structure", song_structure))
        if creative_concept is not None:
            updates.append(("creative_concept", creative_concept))
            
        set_clause = ", ".join(f"{col} = ?" for col, _ in updates)
        params = [val for _, val in updates] + [song_id]
        cursor.execute(f"UPDATE songs SET {set_clause} WHERE id = ?", params)
        
        if sync_ngsl_usage:
            added_targets = new_targets_set - old_targets
            if added_targets:
                placeholders = ",".join("?" * len(added_targets))
                cursor.execute(
                    f"UPDATE ngsl_words SET usage_count = usage_count + 1 WHERE LOWER(word) IN ({placeholders})",
                    list(added_targets)
                )
                
        conn.commit()
        return True


def delete_song(song_id: int, rollback_words: bool = True, db_path: Path = DB_PATH) -> bool:
    """Delete a song by ID from the songs table, optionally rolling back usage counts."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT target_words, bonus_words, reused_words, extra_words FROM songs WHERE id = ?",
            (song_id,)
        )
        row = cursor.fetchone()
        if not row:
            return False
            
        if rollback_words:
            target_raw = row["target_words"] or ""
            bonus_raw = row["bonus_words"] or ""
            reused_raw = (row["reused_words"] if "reused_words" in row.keys() else "") or ""
            extra_raw = row["extra_words"] or ""
            
            ngsl_words = set()
            for w in target_raw.split(","):
                if w.strip():
                    ngsl_words.add(w.strip().lower())
            for w in bonus_raw.split(","):
                if w.strip():
                    ngsl_words.add(w.strip().lower())
            for w in reused_raw.split(","):
                if w.strip():
                    ngsl_words.add(w.strip().lower())
                    
            if ngsl_words:
                placeholders = ",".join("?" * len(ngsl_words))
                cursor.execute(
                    f"UPDATE ngsl_words SET usage_count = MAX(0, usage_count - 1) WHERE LOWER(word) IN ({placeholders})",
                    list(ngsl_words)
                )
                
            extra_words = set()
            for w in extra_raw.split(","):
                if w.strip():
                    extra_words.add(w.strip().lower())
                    
            for extra in extra_words:
                cursor.execute(
                    "UPDATE extra_words SET occurrence_count = occurrence_count - 1 WHERE LOWER(word) = ?",
                    (extra,)
                )
                
            cursor.execute("DELETE FROM extra_words WHERE occurrence_count <= 0")
            
        cursor.execute("DELETE FROM track_variants WHERE song_id = ?", (song_id,))
        cursor.execute("DELETE FROM poster_prompts WHERE song_id = ?", (song_id,))
        cursor.execute("DELETE FROM songs WHERE id = ?", (song_id,))
        conn.commit()
        return True


def migrate_past_songs_bonus_words(db_path: Path = DB_PATH) -> None:
    """Chronological migration for existing songs."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(songs)")
        cols = {row["name"] for row in cursor.fetchall()}
        if "reused_words" not in cols:
            cursor.execute("ALTER TABLE songs ADD COLUMN reused_words TEXT")

        cursor.execute("SELECT id, target_words, bonus_words, reused_words FROM songs ORDER BY id ASC")
        rows = cursor.fetchall()
        
        seen_ngsl: Set[str] = set()
        for r in rows:
            song_id = r["id"]
            target_list = [w.strip().lower() for w in (r["target_words"] or "").split(",") if w.strip()]
            bonus_list = [w.strip().lower() for w in (r["bonus_words"] or "").split(",") if w.strip()]
            existing_reused = [w.strip().lower() for w in (r["reused_words"] or "").split(",") if w.strip()]
            
            seen_ngsl.update(target_list)
            
            new_bonuses = []
            new_reused = list(existing_reused)
            
            for b in bonus_list:
                if b in seen_ngsl:
                    if b not in new_reused:
                        new_reused.append(b)
                else:
                    new_bonuses.append(b)
                    seen_ngsl.add(b)
                    
            cursor.execute(
                "UPDATE songs SET bonus_words = ?, reused_words = ? WHERE id = ?",
                (", ".join(new_bonuses), ", ".join(new_reused), song_id)
            )
        conn.commit()
