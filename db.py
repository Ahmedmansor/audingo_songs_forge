"""
db.py — SQLite database interface for Audingo Songs Forge.
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set
import pandas as pd
import datetime
import zoneinfo

DB_PATH = Path(__file__).parent / "ngsl_vocab.db"


def get_cairo_now_str() -> str:
    """Return current timestamp in Egypt (Africa/Cairo) timezone as YYYY-MM-DD HH:MM:SS."""
    try:
        cairo_tz = zoneinfo.ZoneInfo("Africa/Cairo")
        return datetime.datetime.now(cairo_tz).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")


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

        # Migration: ensure domain column exists in ngsl_words
        cursor.execute("PRAGMA table_info(ngsl_words)")
        existing_ngsl_cols = {row["name"] for row in cursor.fetchall()}
        if "domain" not in existing_ngsl_cols:
            cursor.execute("ALTER TABLE ngsl_words ADD COLUMN domain TEXT DEFAULT NULL")
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
        if "reused_words" not in existing_cols:
            cursor.execute("ALTER TABLE songs ADD COLUMN reused_words TEXT")

        # 4. app_state table (persists active batch across browser refreshes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # 7. studio_drafts table (preserves last 10 approved sessions for recovery)
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

        # Migrate past songs bonus words to cleanly separate first-time bonus vs reused words
        try:
            migrate_past_songs_bonus_words(db_path)
        except Exception:
            pass

        # One-time migration to adjust past song UTC timestamps to Cairo local time (UTC+3)
        try:
            cursor.execute("SELECT value FROM app_state WHERE key = 'cairo_tz_migrated'")
            tz_row = cursor.fetchone()
            if not tz_row or tz_row["value"] != "1":
                cursor.execute("""
                    UPDATE songs
                    SET created_at = datetime(created_at, '+3 hours')
                    WHERE created_at IS NOT NULL
                """)
                cursor.execute("INSERT OR REPLACE INTO app_state (key, value) VALUES ('cairo_tz_migrated', '1')")
                conn.commit()
        except Exception:
            pass


def get_all_ngsl_words(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Retrieve all NGSL words as a pandas DataFrame."""
    with get_connection(db_path) as conn:
        df = pd.read_sql_query(
            "SELECT id, word, domain, pos_type, usage_count, lemma_family FROM ngsl_words ORDER BY word ASC",
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


def get_domain_counts(db_path: Path = DB_PATH) -> Dict[str, int]:
    """Return count of words in each domain."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT domain, COUNT(*) FROM ngsl_words WHERE domain IS NOT NULL GROUP BY domain")
        return {row[0]: row[1] for row in cursor.fetchall()}


def get_domain_detailed_stats(db_path: Path = DB_PATH) -> Dict[str, Dict[str, Any]]:
    """
    Return detailed statistics per domain:
    total words, used words (usage_count > 0), unused/remaining words (usage_count == 0),
    and percentage used.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                domain,
                COUNT(*) as total,
                SUM(CASE WHEN usage_count > 0 THEN 1 ELSE 0 END) as used,
                SUM(CASE WHEN usage_count = 0 THEN 1 ELSE 0 END) as unused
            FROM ngsl_words 
            WHERE domain IS NOT NULL 
            GROUP BY domain
        """)
        rows = cursor.fetchall()
        result = {}
        for r in rows:
            dom = r["domain"]
            tot = r["total"] or 0
            usd = r["used"] or 0
            uns = r["unused"] or 0
            pct_used = (usd / tot * 100) if tot > 0 else 0.0
            result[dom] = {
                "total": tot,
                "used": usd,
                "unused": uns,
                "percent_used": round(pct_used, 1)
            }
        return result



def get_words_domains(words: List[str], db_path: Path = DB_PATH) -> Dict[str, str]:
    """Bulk lookup domain for a list of words."""
    if not words:
        return {}
    cleaned = list({w.strip().lower() for w in words if w.strip()})
    if not cleaned:
        return {}
    placeholders = ",".join("?" * len(cleaned))
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT word, domain FROM ngsl_words WHERE LOWER(word) IN ({placeholders})",
            cleaned
        )
        return {row["word"].lower(): (row["domain"] or "Street & Daily Life") for row in cursor.fetchall()}


def compute_domain_breakdown(words: List[str], db_path: Path = DB_PATH) -> Dict[str, Any]:
    """
    Given a list of words (e.g. target + bonus + reused words in a song),
    computes the percentage and count distribution across the 4 core domains.
    """
    from constants import DOMAINS
    domain_map = get_words_domains(words, db_path=db_path)

    breakdown = {
        d: {"count": 0, "percent": 0.0, "words": []} for d in DOMAINS
    }

    classified_count = 0
    for w in words:
        w_clean = w.strip().lower()
        dom = domain_map.get(w_clean, "Street & Daily Life")
        if dom not in breakdown:
            dom = "Street & Daily Life"
        breakdown[dom]["count"] += 1
        breakdown[dom]["words"].append(w.strip())
        classified_count += 1

    # Calculate percentages
    primary_domain = DOMAINS[0]
    max_pct = 0.0
    for d, data in breakdown.items():
        pct = round((data["count"] / classified_count * 100), 1) if classified_count > 0 else 0.0
        data["percent"] = pct
        if pct > max_pct:
            max_pct = pct
            primary_domain = d

    formal_pct = breakdown.get("Business & Career", {}).get("percent", 0.0) + breakdown.get("Society, Law & Deep Ideas", {}).get("percent", 0.0)
    is_high_formal = formal_pct >= 25.0

    return {
        "total_words": classified_count,
        "domains": breakdown,
        "primary_domain": primary_domain,
        "primary_percent": max_pct,
        "is_high_formal": is_high_formal,
        "formal_percent": round(formal_pct, 1)
    }


def pull_20_words(domain: Optional[str] = None, db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """
    Randomly select 20 words where usage_count = 0 according to ratio:
    - 50% Nouns (10 words)
    - 30% Verbs (6 words)
    - 20% Adjectives (4 words)
    If domain is specified, filters words by domain with graceful fallback.
    """
    targets = [
        ("Noun", 10),
        ("Verb", 6),
        ("Adjective", 4)
    ]
    
    selected_words: List[Dict[str, Any]] = []
    use_domain = domain if (domain and domain != "All Domains" and "الكل" not in domain and "All" not in domain) else None
    
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        for pos, count in targets:
            if use_domain:
                query = """
                    SELECT id, word, lemma_family, pos_type, usage_count, domain
                    FROM ngsl_words
                    WHERE usage_count = 0 AND pos_type = ? AND domain = ?
                    ORDER BY RANDOM()
                    LIMIT ?
                """
                params = (pos, use_domain, count)
            else:
                query = """
                    SELECT id, word, lemma_family, pos_type, usage_count, domain
                    FROM ngsl_words
                    WHERE usage_count = 0 AND pos_type = ?
                    ORDER BY RANDOM()
                    LIMIT ?
                """
                params = (pos, count)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for r in rows:
                selected_words.append({
                    "id": r["id"],
                    "word": r["word"],
                    "lemma_family": r["lemma_family"],
                    "pos_type": r["pos_type"],
                    "usage_count": r["usage_count"],
                    "domain": r["domain"] if "domain" in r.keys() else "Street & Daily Life"
                })
                
        # If any category had fewer words than needed, fill the remainder
        if len(selected_words) < 20:
            existing_ids = [w["id"] for w in selected_words]
            needed = 20 - len(selected_words)
            placeholders = ",".join("?" * len(existing_ids)) if existing_ids else ""
            
            # First try within the same domain if specified
            if use_domain:
                id_clause = f"AND id NOT IN ({placeholders})" if existing_ids else ""
                query = f"""
                    SELECT id, word, lemma_family, pos_type, usage_count, domain
                    FROM ngsl_words
                    WHERE usage_count = 0 AND domain = ? {id_clause}
                    ORDER BY RANDOM()
                    LIMIT ?
                """
                params = [use_domain] + existing_ids + [needed] if existing_ids else [use_domain, needed]
                cursor.execute(query, params)
                for r in cursor.fetchall():
                    selected_words.append({
                        "id": r["id"],
                        "word": r["word"],
                        "lemma_family": r["lemma_family"],
                        "pos_type": r["pos_type"],
                        "usage_count": r["usage_count"],
                        "domain": r["domain"] if "domain" in r.keys() else "Street & Daily Life"
                    })
            
            # If still under 20, fill from any domain
            if len(selected_words) < 20:
                existing_ids = [w["id"] for w in selected_words]
                needed = 20 - len(selected_words)
                id_clause = f"WHERE usage_count = 0 AND id NOT IN ({','.join('?' * len(existing_ids))})" if existing_ids else "WHERE usage_count = 0"
                params = existing_ids + [needed] if existing_ids else [needed]
                query = f"""
                    SELECT id, word, lemma_family, pos_type, usage_count, domain
                    FROM ngsl_words
                    {id_clause}
                    ORDER BY RANDOM()
                    LIMIT ?
                """
                cursor.execute(query, params)
                for r in cursor.fetchall():
                    selected_words.append({
                        "id": r["id"],
                        "word": r["word"],
                        "lemma_family": r["lemma_family"],
                        "pos_type": r["pos_type"],
                        "usage_count": r["usage_count"],
                        "domain": r["domain"] if "domain" in r.keys() else "Street & Daily Life"
                    })

    return selected_words


def pull_candidate_pool_for_thematic_curation(
    nouns_limit: int = 70,
    verbs_limit: int = 40,
    adjs_limit: int = 30,
    domain: Optional[str] = None,
    db_path: Path = DB_PATH
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Randomly select candidate pool of unused words (usage_count = 0)
    for thematic AI curation:
    - 70 Nouns
    - 40 Verbs
    - 30 Adjectives
    Total: 140 candidate words.
    If domain is specified, filters words within that domain with graceful fallback.
    """
    candidate_targets = [
        ("Noun", nouns_limit),
        ("Verb", verbs_limit),
        ("Adjective", adjs_limit)
    ]
    pool: Dict[str, List[Dict[str, Any]]] = {
        "Noun": [],
        "Verb": [],
        "Adjective": []
    }
    use_domain = domain if (domain and domain != "All Domains" and "الكل" not in domain and "All" not in domain) else None

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        for pos, count in candidate_targets:
            if use_domain:
                cursor.execute(
                    """
                    SELECT id, word, lemma_family, pos_type, usage_count, domain
                    FROM ngsl_words
                    WHERE usage_count = 0 AND pos_type = ? AND domain = ?
                    ORDER BY RANDOM()
                    LIMIT ?
                    """,
                    (pos, use_domain, count)
                )
            else:
                cursor.execute(
                    """
                    SELECT id, word, lemma_family, pos_type, usage_count, domain
                    FROM ngsl_words
                    WHERE usage_count = 0 AND pos_type = ?
                    ORDER BY RANDOM()
                    LIMIT ?
                    """,
                    (pos, count)
                )
            for r in cursor.fetchall():
                pool[pos].append({
                    "id": r["id"],
                    "word": r["word"],
                    "lemma_family": r["lemma_family"],
                    "pos_type": r["pos_type"],
                    "usage_count": r["usage_count"],
                    "domain": r["domain"] if "domain" in r.keys() else "Street & Daily Life"
                })

            # If that domain didn't have enough candidates, top up from other domains so Gemini has ample choices
            if use_domain and len(pool[pos]) < count:
                existing_ids = [w["id"] for w in pool[pos]]
                needed = count - len(pool[pos])
                placeholders = ",".join("?" * len(existing_ids)) if existing_ids else ""
                id_clause = f"AND id NOT IN ({placeholders})" if existing_ids else ""
                topup_query = f"""
                    SELECT id, word, lemma_family, pos_type, usage_count, domain
                    FROM ngsl_words
                    WHERE usage_count = 0 AND pos_type = ? {id_clause}
                    ORDER BY RANDOM()
                    LIMIT ?
                """
                params = [pos] + existing_ids + [needed] if existing_ids else [pos, needed]
                cursor.execute(topup_query, params)
                for r in cursor.fetchall():
                    pool[pos].append({
                        "id": r["id"],
                        "word": r["word"],
                        "lemma_family": r["lemma_family"],
                        "pos_type": r["pos_type"],
                        "usage_count": r["usage_count"],
                        "domain": r["domain"] if "domain" in r.keys() else "Street & Daily Life"
                    })

    return pool


def build_curated_batch_from_words(
    selected_nouns: List[str],
    selected_verbs: List[str],
    selected_adjs: List[str],
    candidate_pool: Dict[str, List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Map selected word strings back to full SQLite record dicts,
    strictly ensuring exactly 10 Nouns, 6 Verbs, and 4 Adjectives (20 words total).
    Any shortfall is safely backfilled from the candidate pool.
    """
    final_batch: List[Dict[str, Any]] = []
    used_ids: Set[int] = set()

    def process_pos(selected_words: List[str], pos: str, target_count: int):
        candidates = candidate_pool.get(pos, [])
        word_map = {c["word"].lower().strip(): c for c in candidates}
        added_count = 0
        
        # 1. Add matching words from selection
        for w in selected_words:
            w_clean = w.lower().strip()
            if w_clean in word_map:
                item = word_map[w_clean]
                if item["id"] not in used_ids and added_count < target_count:
                    final_batch.append(item)
                    used_ids.add(item["id"])
                    added_count += 1

        # 2. If short, backfill from candidate pool
        if added_count < target_count:
            for item in candidates:
                if item["id"] not in used_ids and added_count < target_count:
                    final_batch.append(item)
                    used_ids.add(item["id"])
                    added_count += 1

    process_pos(selected_nouns, "Noun", 10)
    process_pos(selected_verbs, "Verb", 6)
    process_pos(selected_adjs, "Adjective", 4)

    return final_batch


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


def get_used_ngsl_words(db_path: Path = DB_PATH) -> Set[str]:
    """Retrieve set of all lowercased NGSL words that have usage_count > 0."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT LOWER(word) FROM ngsl_words WHERE usage_count > 0")
        return {row[0].strip() for row in cursor.fetchall() if row[0]}


# Comprehensive white-list of structural words and indispensable daily conversational vocabulary
# These words must NEVER be placed in the avoidance list so that songwriting remains 100% natural.
CORE_EXEMPT_WORDS: Set[str] = {
    # Pronouns & Determiners
    "i", "me", "my", "myself", "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "it", "its", "itself", "we", "us", "our", "ours", "ourselves",
    "they", "them", "their", "theirs", "themselves",
    "this", "that", "these", "those", "who", "whom", "whose", "which", "what", "whatever", "whoever",
    # Prepositions, Particles, Articles & Conjunctions
    "a", "an", "the", "in", "on", "at", "by", "for", "with", "about", "against", "between",
    "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down",
    "out", "off", "over", "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "and", "but", "if", "or", "because", "as", "until", "while", "of", "since", "although", "though",
    "whether", "unless", "till", "yet", "can", "could", "will", "would", "shall", "should", "may",
    "might", "must", "just", "now", "don't", "doesn't", "didn't", "won't", "wouldn't", "can't",
    "cannot", "couldn't", "shouldn't", "isn't", "aren't", "wasn't", "weren't", "haven't", "hasn't",
    "hadn't", "let's", "i'm", "you're", "he's", "she's", "it's", "we're", "they're", "i've",
    "you've", "we've", "they've", "i'll", "you'll", "he'll", "she'll", "we'll", "they'll", "i'd",
    # Indispensable Everyday Verbs (and their natural inflections)
    "be", "am", "is", "are", "was", "were", "been", "being",
    "have", "has", "had", "having",
    "do", "does", "did", "doing", "done",
    "go", "goes", "went", "gone", "going",
    "get", "gets", "got", "gotten", "getting",
    "make", "makes", "made", "making",
    "take", "takes", "took", "taken", "taking",
    "come", "comes", "came", "coming",
    "see", "sees", "saw", "seen", "seeing",
    "know", "knows", "knew", "known", "knowing",
    "think", "thinks", "thought", "thinking",
    "look", "looks", "looked", "looking",
    "want", "wants", "wanted", "wanting",
    "give", "gives", "gave", "given", "giving",
    "tell", "tells", "told", "telling",
    "say", "says", "said", "saying",
    "feel", "feels", "felt", "feeling",
    "find", "finds", "found", "finding",
    "ask", "asks", "asked", "asking",
    "seem", "seems", "seemed", "seeming",
    "leave", "leaves", "left", "leaving",
    "call", "calls", "called", "calling",
    "keep", "keeps", "kept", "keeping",
    "let", "lets", "letting",
    "put", "puts", "putting",
    "try", "tries", "tried", "trying",
    "start", "starts", "started", "starting",
    "show", "shows", "showed", "shown", "showing",
    "hear", "hears", "heard", "hearing",
    "play", "plays", "played", "playing",
    "run", "runs", "ran", "running",
    "move", "moves", "moved", "moving",
    "live", "lives", "lived", "living",
    "turn", "turns", "turned", "turning",
    "bring", "brings", "brought", "bringing",
    "hold", "holds", "held", "holding",
    "write", "writes", "wrote", "written", "writing",
    "stand", "stands", "stood", "standing",
    "sit", "sits", "sat", "sitting",
    "lose", "loses", "lost", "losing",
    "pay", "pays", "paid", "paying",
    "meet", "meets", "met", "meeting",
    "include", "includes", "included", "including",
    "continue", "continues", "continued", "continuing",
    "set", "sets", "setting",
    "learn", "learns", "learned", "learning",
    "change", "changes", "changed", "changing",
    "lead", "leads", "led", "leading",
    "understand", "understands", "understood", "understanding",
    "watch", "watches", "watched", "watching",
    "follow", "follows", "followed", "following",
    "stop", "stops", "stopped", "stopping",
    "create", "creates", "created", "creating",
    "speak", "speaks", "spoke", "spoken", "speaking",
    "read", "reads", "reading",
    "spend", "spends", "spent", "spending",
    "grow", "grows", "grew", "grown", "growing",
    "open", "opens", "opened", "opening",
    "walk", "walks", "walked", "walking",
    "win", "wins", "won", "winning",
    "teach", "teaches", "taught", "teaching",
    "offer", "offers", "offered", "offering",
    "remember", "remembers", "remembered", "remembering",
    "consider", "considers", "considered", "considering",
    "love", "loves", "loved", "loving",
    "buy", "buys", "bought", "buying",
    "wait", "waits", "waited", "waiting",
    "serve", "serves", "served", "serving",
    "die", "dies", "died", "dying",
    "send", "sends", "sent", "sending",
    "expect", "expects", "expected", "expecting",
    "build", "builds", "built", "building",
    "stay", "stays", "stayed", "staying",
    "fall", "falls", "fell", "fallen", "falling",
    "cut", "cuts", "cutting",
    "reach", "reaches", "reached", "reaching",
    "kill", "kills", "killed", "killing",
    "remain", "remains", "remained", "remaining",
    "pass", "passes", "passed", "passing",
    "sell", "sells", "sold", "selling",
    "require", "requires", "required", "requiring",
    "report", "reports", "reported", "reporting",
    "decide", "decides", "decided", "deciding",
    "pull", "pulls", "pulled", "pulling",
    "break", "breaks", "broke", "broken", "breaking",
    "hope", "hopes", "hoped", "hoping",
    "wish", "wishes", "wished", "wishing",
    "laugh", "laughs", "laughed", "laughing",
    "smile", "smiles", "smiled", "smiling",
    "talk", "talks", "talked", "talking",
    "listen", "listens", "listened", "listening",
    "work", "works", "worked", "working",
    "help", "helps", "helped", "helping",
    "need", "needs", "needed", "needing",
    # Indispensable Conversational Nouns & Adjectives
    "time", "times", "year", "years", "people", "way", "ways", "day", "days",
    "man", "men", "woman", "women", "life", "lives", "child", "children",
    "world", "school", "state", "family", "student", "group", "country",
    "problem", "hand", "hands", "part", "place", "places", "case", "week", "weeks",
    "company", "system", "program", "question", "work", "night", "nights",
    "point", "home", "water", "room", "mother", "area", "money", "story",
    "fact", "month", "months", "lot", "right", "study", "book", "eye", "eyes",
    "job", "word", "words", "business", "issue", "side", "kind", "head",
    "house", "service", "friend", "friends", "father", "power", "hour", "hours",
    "game", "line", "end", "member", "law", "car", "city", "community", "name",
    "morning", "evening", "tonight", "today", "tomorrow", "yesterday",
    "good", "new", "first", "last", "long", "great", "little", "own", "other",
    "old", "right", "big", "high", "different", "small", "large", "next",
    "early", "young", "important", "few", "public", "bad", "same", "able",
    "well", "better", "best", "simple", "sure", "fine", "true", "false",
    "easy", "hard", "real", "clear", "ready", "happy", "alright",
    "thing", "things", "something", "anything", "nothing", "everything",
    "someone", "anyone", "everyone", "no one", "nobody", "somebody", "anybody",
    "everywhere", "somewhere", "anywhere", "nowhere",
    "always", "never", "ever", "often", "sometimes", "usually", "really",
    "together", "back", "away", "still", "even", "almost", "enough",
    "maybe", "perhaps", "please", "thanks", "thank", "yeah", "yes", "no", "oh", "hey", "okay", "ok"
}


def get_previously_used_words(
    exclude_words: Optional[List[str]] = None,
    db_path: Path = DB_PATH
) -> List[str]:
    """
    Return list of content words previously used (usage_count > 0),
    strictly excluding current batch targets, structural grammar words,
    and all indispensable basic conversational English words.
    """
    exclude_set = {w.lower().strip() for w in (exclude_words or []) if w.strip()}

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT LOWER(word) FROM ngsl_words WHERE usage_count > 0 ORDER BY word ASC")
        rows = cursor.fetchall()

    filtered = [
        r[0].strip() for r in rows
        if r[0] and r[0].strip() not in exclude_set and r[0].strip() not in CORE_EXEMPT_WORDS and len(r[0].strip()) > 1
    ]
    return filtered


def migrate_past_songs_bonus_words(db_path: Path = DB_PATH) -> None:
    """
    Chronological migration for existing songs:
    Ensures bonus_words only retains words on their FIRST appearance as bonus across songs.
    Moves subsequent repeats of the word in later songs to reused_words.
    Leaves ngsl_words.usage_count completely untouched.
    """
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


def approve_and_save_song(
    title: str,
    lyrics: str,
    target_words: List[str],
    checked_bonus_words: List[str],  # Blue words checked (new bonus words)
    checked_extra_words: List[str],  # Yellow words checked
    checked_target_words: Optional[List[str]] = None, # Green words checked
    reused_words: Optional[List[str]] = None, # White words (previously covered)
    mood_breakdown: Optional[Dict[str, Any]] = None,
    genre: str = "",
    song_structure: str = "",
    creative_concept: str = "",
    db_path: Path = DB_PATH
) -> Tuple[int, int, int]:
    """
    Approve and save song:
    1. Insert into songs table (target_words, bonus_words, reused_words, extra_words, mood_breakdown, genre, song_structure, creative_concept).
    2. Increment usage_count for Target + Bonus + Reused NGSL words.
    3. Insert or increment occurrence_count for checked Yellow extra_words.
    Returns (song_id, approved_ngsl_count, approved_extra_count).
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Determine actual NGSL words approved
        actual_target_words = checked_target_words if checked_target_words is not None else target_words
        target_words_str = ", ".join(actual_target_words)
        bonus_words_str = ", ".join(checked_bonus_words)
        reused_words_str = ", ".join(reused_words or [])
        extra_words_str = ", ".join(checked_extra_words)
        mood_json = json.dumps(mood_breakdown) if isinstance(mood_breakdown, dict) else (mood_breakdown or "")

        # 1. Insert song
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
        
        # 2. Increment usage_count in ngsl_words for approved target + bonus + reused words
        all_ngsl_to_increment = actual_target_words + checked_bonus_words + (reused_words or [])
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
            
            # Decrement NGSL words (Target + Bonus + Reused)
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
    selected_domain: str = "All Domains",
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


# ══════════════════════════════════════════════════════════════════════════════
# STUDIO DRAFTS — Approved session snapshots (survives song deletion)
# ══════════════════════════════════════════════════════════════════════════════

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
    """
    Snapshot the current studio session as a named draft right before
    approval clears the active batch. Keeps only the most recent
    ``max_drafts`` entries (oldest are pruned automatically).
    """
    # Build a human-readable label: first 4 word names + song title
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
        # Prune oldest rows if we exceed the limit
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
    """
    Return all saved studio drafts, newest first.
    Each dict has keys: id, song_title, label, saved_at.
    """
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
