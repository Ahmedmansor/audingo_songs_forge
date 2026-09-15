"""
connection.py — Database connection, Cairo time helper, and schema initialization.
"""

import datetime
import zoneinfo
import sqlite3
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT_DIR / "ngsl_vocab.db"


def get_cairo_now_str() -> str:
    """Return current timestamp in Egypt (Africa/Cairo) timezone as YYYY-MM-DD HH:MM:SS."""
    try:
        cairo_tz = zoneinfo.ZoneInfo("Africa/Cairo")
        return datetime.datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Returns a configured SQLite connection with row factory."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    """Initializes all database tables and indexes."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. ngsl_words table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ngsl_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL,
                lemma_family TEXT NOT NULL,
                pos_type TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0,
                domain TEXT DEFAULT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ngsl_word ON ngsl_words(word);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ngsl_usage ON ngsl_words(usage_count);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ngsl_pos ON ngsl_words(pos_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ngsl_domain ON ngsl_words(domain);")

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
                song_structure TEXT,
                creative_concept TEXT,
                reused_words TEXT,
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
        if "reused_words" not in existing_cols:
            cursor.execute("ALTER TABLE songs ADD COLUMN reused_words TEXT")

        # 4. app_state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # 5. studio_drafts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS studio_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_title TEXT NOT NULL,
                label TEXT NOT NULL,
                session_json TEXT NOT NULL,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_draft_saved ON studio_drafts(saved_at DESC);")

        # 6. poster_prompts table
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

        # 7. track_variants table
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

        conn.commit()
