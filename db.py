"""
db.py — SQLite database interface for Audingo Songs Forge.
"""

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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
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
    checked_ngsl_words: List[str],  # Green and Blue words checked
    checked_extra_words: List[str], # Yellow words checked
    db_path: Path = DB_PATH
) -> Tuple[int, int, int]:
    """
    Approve and save song:
    1. Insert into songs table.
    2. Increment usage_count for checked Green/Blue NGSL words.
    3. Insert or increment occurrence_count for checked Yellow extra_words.
    Returns (song_id, approved_ngsl_count, approved_extra_count).
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. Insert song
        target_words_str = ", ".join(target_words)
        cursor.execute(
            "INSERT INTO songs (title, lyrics, target_words) VALUES (?, ?, ?)",
            (title, lyrics, target_words_str)
        )
        song_id = cursor.lastrowid
        
        # 2. Increment usage_count in ngsl_words
        unique_ngsl = list(set([w.lower().strip() for w in checked_ngsl_words if w.strip()]))
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
