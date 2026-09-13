"""
db.py — SQLite database interface for Audingo Songs Forge.
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

DB_PATH = Path(__file__).parent / "ngsl_vocab.db"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Return a connection to the SQLite database with Row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    """Initialize SQLite database tables if they do not exist."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. ngsl_words table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ngsl_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL,
                lemma_family TEXT NOT NULL,
                pos_type TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ngsl_word ON ngsl_words(word);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ngsl_usage ON ngsl_words(usage_count);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ngsl_pos ON ngsl_words(pos_type);")

        # 2. extra_words table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extra_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL,
                occurrence_count INTEGER DEFAULT 1,
                first_seen_in_song TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_extra_word ON extra_words(word);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_extra_count ON extra_words(occurrence_count DESC);")

        # 3. songs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                lyrics TEXT NOT NULL,
                target_words TEXT NOT NULL,
                bonus_words TEXT,
                extra_words TEXT,
                mood_breakdown TEXT,
                genre TEXT,
                creative_concept TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration: ensure new columns exist in existing songs table
        cursor.execute("PRAGMA table_info(songs)")
        existing_cols = {row["name"] for row in cursor.fetchall()}
        if "bonus_words" not in existing_cols:
            cursor.execute("ALTER TABLE songs ADD COLUMN bonus_words TEXT")
        if "extra_words" not in existing_cols:
            cursor.execute("ALTER TABLE songs ADD COLUMN extra_words TEXT")
        if "mood_breakdown" not in existing_cols:
            cursor.execute("ALTER TABLE songs ADD COLUMN mood_breakdown TEXT")
        if "genre" not in existing_cols:
            cursor.execute("ALTER TABLE songs ADD COLUMN genre TEXT")
        if "song_structure" not in existing_cols:
            cursor.execute("ALTER TABLE songs ADD COLUMN song_structure TEXT")
        if "creative_concept" not in existing_cols:
            cursor.execute("ALTER TABLE songs ADD COLUMN creative_concept TEXT")

        # 4. app_state table (persists active batch across browser refreshes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # 5. poster_prompts table (legacy / backwards compatibility)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS poster_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_id INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
                genre TEXT NOT NULL,
                vocalist TEXT NOT NULL,
                prompt_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(song_id, genre, vocalist)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_poster_song ON poster_prompts(song_id);")

        # 6. track_variants table (Packaging System: Suno Music Prompt + Midjourney/DALL-E Poster Prompt)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS track_variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_id INTEGER NOT NULL REFERENCES songs(id) ON DELETE CASCADE,
                genre TEXT NOT NULL,
                vocalist TEXT NOT NULL,
                suno_prompt TEXT NOT NULL,
                poster_prompt TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(song_id, genre, vocalist)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_variant_song ON track_variants(song_id);")

        # Automatic migration from poster_prompts if exists
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO track_variants (song_id, genre, vocalist, suno_prompt, poster_prompt, created_at)
                SELECT song_id, genre, vocalist, 
                       genre || ', steady tempo, clear upfront ' || LOWER(vocalist) || ' vocals, clean mix',
                       prompt_text, created_at
                FROM poster_prompts
            """)
        except Exception:
            pass

        conn.commit()


def get_all_ngsl_words(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Retrieve all NGSL words as a pandas DataFrame."""
    with get_connection(db_path) as conn:
        df = pd.read_sql_query(
            "SELECT id, word, pos_type, usage_count, lemma_family FROM ngsl_words ORDER BY word ASC",
            conn
        )
        return df


def get_extra_words(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Retrieve all extra words sorted descending by occurrence_count."""
    with get_connection(db_path) as conn:
        df = pd.read_sql_query(
            "SELECT id, word, occurrence_count, first_seen_in_song FROM extra_words ORDER BY occurrence_count DESC, word ASC",
            conn
        )
        return df


def get_progress_stats(db_path: Path = DB_PATH) -> Dict[str, Any]:
    """Return dictionary progress statistics."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ngsl_words")
        total = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM ngsl_words WHERE usage_count > 0")
        used = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM extra_words")
        extra_count = cursor.fetchone()[0] or 0

        unused = total - used
        percent = (used / total * 100) if total > 0 else 0.0

        return {
            "total": total,
            "used": used,
            "unused": unused,
            "percent": round(percent, 1),
            "extra_count": extra_count
        }


def pull_20_words(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """
    Randomly select 20 words where usage_count = 0 according to ratio:
    - 50% Nouns (10 words)
    - 30% Verbs (6 words)
    - 20% Adjectives (4 words)
    """
    targets = [
        ("Noun", 10),
        ("Verb", 6),
        ("Adjective", 4)
    ]
    
    selected_words: List[Dict[str, Any]] = []
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        for pos, count in targets:
            cursor.execute(
                """
                SELECT id, word, lemma_family, pos_type, usage_count
                FROM ngsl_words
                WHERE usage_count = 0 AND pos_type = ?
                ORDER BY RANDOM()
                LIMIT ?
                """,
                (pos, count)
            )
            rows = cursor.fetchall()
            for r in rows:
                selected_words.append({
                    "id": r["id"],
                    "word": r["word"],
                    "lemma_family": r["lemma_family"],
                    "pos_type": r["pos_type"],
                    "usage_count": r["usage_count"]
                })
                
        # If any category had fewer words than needed, fill the remainder with any unused words
        if len(selected_words) < 20:
            existing_ids = [w["id"] for w in selected_words]
            needed = 20 - len(selected_words)
            if existing_ids:
                placeholders = ",".join("?" * len(existing_ids))
                query = f"""
                    SELECT id, word, lemma_family, pos_type, usage_count
                    FROM ngsl_words
                    WHERE usage_count = 0 AND id NOT IN ({placeholders})
                    ORDER BY RANDOM()
                    LIMIT ?
                """
                params = existing_ids + [needed]
            else:
                query = """
                    SELECT id, word, lemma_family, pos_type, usage_count
                    FROM ngsl_words
                    WHERE usage_count = 0
                    ORDER BY RANDOM()
                    LIMIT ?
                """
                params = [needed]
            cursor.execute(query, params)
            for r in cursor.fetchall():
                selected_words.append({
                    "id": r["id"],
                    "word": r["word"],
                    "lemma_family": r["lemma_family"],
                    "pos_type": r["pos_type"],
                    "usage_count": r["usage_count"]
                })

    return selected_words


def swap_single_word(
    pos_type: str,
    current_word_ids: List[int],
    db_path: Path = DB_PATH
) -> Optional[Dict[str, Any]]:
    """
    Replace one word with another unused word of the SAME pos_type,
    excluding all words currently in the batch.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        placeholders = ",".join("?" * len(current_word_ids)) if current_word_ids else "0"
        query = f"""
            SELECT id, word, lemma_family, pos_type, usage_count
            FROM ngsl_words
            WHERE usage_count = 0 AND pos_type = ? AND id NOT IN ({placeholders})
            ORDER BY RANDOM()
            LIMIT 1
        """
        params = [pos_type] + current_word_ids
        cursor.execute(query, params)
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "word": row["word"],
                "lemma_family": row["lemma_family"],
                "pos_type": row["pos_type"],
                "usage_count": row["usage_count"]
            }
    return None


def get_all_lemma_mappings(db_path: Path = DB_PATH) -> Dict[str, str]:
    """
    Returns a dictionary mapping every inflected form to its headword.
    e.g. {'abstract': 'abstract', 'abstracts': 'abstract', 'abstracting': 'abstract', ...}
    Also returns headword info for fast lookup in memory.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT word, lemma_family FROM ngsl_words")
        rows = cursor.fetchall()
        
        lemma_to_headword = {}
        for row in rows:
            headword = row["word"].strip().lower()
            lemma_to_headword[headword] = headword
            family_str = row["lemma_family"]
            if family_str:
                for form in family_str.split(","):
                    form_clean = form.strip().lower()
                    if form_clean:
                        lemma_to_headword[form_clean] = headword
        return lemma_to_headword


def approve_and_save_song(
    title: str,
    lyrics: str,
    target_words: List[str],
    checked_bonus_words: List[str],  # Blue words checked
    checked_extra_words: List[str],  # Yellow words checked
    checked_target_words: Optional[List[str]] = None, # Green words checked
    mood_breakdown: Optional[Dict[str, Any]] = None,
    genre: str = "",
    song_structure: str = "",
    creative_concept: str = "",
    db_path: Path = DB_PATH
) -> Tuple[int, int, int]:
    """
    Approve and save song:
    1. Insert into songs table (target_words, bonus_words, extra_words, mood_breakdown, genre, song_structure, creative_concept).
    2. Increment usage_count for checked Green + Blue NGSL words.
    3. Insert or increment occurrence_count for checked Yellow extra_words.
    Returns (song_id, approved_ngsl_count, approved_extra_count).
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Determine actual NGSL words approved
        actual_target_words = checked_target_words if checked_target_words is not None else target_words
        target_words_str = ", ".join(actual_target_words)
        bonus_words_str = ", ".join(checked_bonus_words)
        extra_words_str = ", ".join(checked_extra_words)
        mood_json = json.dumps(mood_breakdown) if isinstance(mood_breakdown, dict) else (mood_breakdown or "")

        # 1. Insert song
        cursor.execute(
            """
            INSERT INTO songs (
                title, lyrics, target_words, bonus_words, extra_words,
                mood_breakdown, genre, song_structure, creative_concept
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title, lyrics, target_words_str, bonus_words_str, extra_words_str,
                mood_json, genre, song_structure, creative_concept
            )
        )
        song_id = cursor.lastrowid
        
        # 2. Increment usage_count in ngsl_words for approved target + bonus words
        all_ngsl_to_increment = actual_target_words + checked_bonus_words
        unique_ngsl = list(set([w.lower().strip() for w in all_ngsl_to_increment if w.strip()]))
        if unique_ngsl:
            placeholders = ",".join("?" * len(unique_ngsl))
            cursor.execute(
                f"UPDATE ngsl_words SET usage_count = usage_count + 1 WHERE LOWER(word) IN ({placeholders})",
                unique_ngsl
            )
            
        # 3. Insert or update in extra_words
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
            "SELECT id, title, lyrics, target_words, bonus_words, extra_words, mood_breakdown, genre, song_structure, creative_concept, created_at FROM songs ORDER BY id DESC",
            conn
        )
        return df


def update_song(
    song_id: int,
    title: str,
    lyrics: str,
    target_words: str,
    bonus_words: Optional[str] = None,
    extra_words: Optional[str] = None,
    mood_breakdown: Optional[Dict[str, Any]] = None,
    genre: Optional[str] = None,
    song_structure: Optional[str] = None,
    creative_concept: Optional[str] = None,
    sync_ngsl_usage: bool = True,
    db_path: Path = DB_PATH
) -> bool:
    """
    Update an existing song's details and metadata in SQLite.
    If sync_ngsl_usage is True, checks target_words against ngsl_words and ensures
    their usage_count is incremented if newly added.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. Fetch current song row to compare target words
        cursor.execute("SELECT target_words, bonus_words, extra_words, title FROM songs WHERE id = ?", (song_id,))
        row = cursor.fetchone()
        if not row:
            return False
            
        old_targets = set(w.strip().lower() for w in (row["target_words"] or "").split(",") if w.strip())
        new_targets_list = [w.strip() for w in target_words.split(",") if w.strip()]
        new_targets_set = set(w.lower() for w in new_targets_list)
        
        # 2. Update song table
        updates = [
            ("title", title),
            ("lyrics", lyrics),
            ("target_words", ", ".join(new_targets_list))
        ]
        if bonus_words is not None:
            new_bonuses = [w.strip() for w in bonus_words.split(",") if w.strip()]
            updates.append(("bonus_words", ", ".join(new_bonuses)))
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
        
        # 3. If sync_ngsl_usage is requested, increment usage_count for newly added target words
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
    """
    Delete a song by ID from the songs table.
    If rollback_words is True, executes an atomic rollback:
    - Decrements usage_count (-1) in ngsl_words for all target and bonus words associated with this song.
    - Decrements occurrence_count (-1) in extra_words for all extra words, and deletes any that reach 0.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. Fetch song row before deleting
        cursor.execute(
            "SELECT target_words, bonus_words, extra_words FROM songs WHERE id = ?",
            (song_id,)
        )
        row = cursor.fetchone()
        if not row:
            return False
            
        if rollback_words:
            target_raw = row["target_words"] or ""
            bonus_raw = row["bonus_words"] or ""
            extra_raw = row["extra_words"] or ""
            
            # Decrement NGSL words (Target + Bonus)
            ngsl_words = set()
            for w in target_raw.split(","):
                if w.strip():
                    ngsl_words.add(w.strip().lower())
            for w in bonus_raw.split(","):
                if w.strip():
                    ngsl_words.add(w.strip().lower())
                    
            if ngsl_words:
                placeholders = ",".join("?" * len(ngsl_words))
                cursor.execute(
                    f"UPDATE ngsl_words SET usage_count = MAX(0, usage_count - 1) WHERE LOWER(word) IN ({placeholders})",
                    list(ngsl_words)
                )
                
            # Decrement Extra words
            extra_words = set()
            for w in extra_raw.split(","):
                if w.strip():
                    extra_words.add(w.strip().lower())
                    
            for extra in extra_words:
                cursor.execute(
                    "UPDATE extra_words SET occurrence_count = occurrence_count - 1 WHERE LOWER(word) = ?",
                    (extra,)
                )
                
            # Clean up extra words whose occurrence reached <= 0
            cursor.execute("DELETE FROM extra_words WHERE occurrence_count <= 0")
            
        # 2. Delete associated track variants and poster prompts
        cursor.execute("DELETE FROM track_variants WHERE song_id = ?", (song_id,))
        cursor.execute("DELETE FROM poster_prompts WHERE song_id = ?", (song_id,))

        # 3. Delete the song row
        cursor.execute("DELETE FROM songs WHERE id = ?", (song_id,))
        conn.commit()
        return True


def upsert_track_variant(
    song_id: int,
    genre: str,
    vocalist: str,
    suno_prompt: str,
    poster_prompt: str,
    db_path: Path = DB_PATH
) -> int:
    """
    Insert or update a track variant (Suno music prompt + poster prompt) for (song_id, genre, vocalist).
    If (song_id, genre, vocalist) exists, it overrides both prompts and refreshes timestamp.
    """
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


# Alias for upsert_track_variant
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
    """
    Insert or update a poster prompt for a (song_id, genre, vocalist) combination.
    If the combination already exists, it overrides the prompt_text and updates timestamp.
    """
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
    db_path: Path = DB_PATH
) -> None:
    """Save active studio batch state to app_state table in SQLite for persistence across browser refreshes."""
    payload = {
        "target_batch": batch,
        "custom_concept": concept,
        "selected_genre": genre,
        "selected_structure": song_structure,
        "mood_analysis": mood_analysis,
        "master_prompt": master_prompt,
        "suno_prompt": suno_prompt,
        "poster_prompt": poster_prompt,
        "selected_vocalist": vocalist
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
