"""
word_repository.py — Repository for NGSL words, extra words, batch pulling, and vocab analytics.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import pandas as pd
from data.database.connection import get_connection, DB_PATH
from constants import DOMAINS


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
    """Return detailed statistics per domain: total, used, unused, percent_used."""
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
    """Given a list of words, computes the percentage and count distribution across the 4 core domains."""
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
                
        if len(selected_words) < 20:
            existing_ids = [w["id"] for w in selected_words]
            needed = 20 - len(selected_words)
            placeholders = ",".join("?" * len(existing_ids)) if existing_ids else ""
            
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
    """Randomly select candidate pool of unused words (usage_count = 0) for thematic AI curation."""
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
    """Map selected word strings back to full SQLite record dicts, ensuring 10 Nouns, 6 Verbs, 4 Adjectives."""
    final_batch: List[Dict[str, Any]] = []
    used_ids: Set[int] = set()

    def process_pos(selected_words: List[str], pos: str, target_count: int):
        candidates = candidate_pool.get(pos, [])
        word_map = {c["word"].lower().strip(): c for c in candidates}
        added_count = 0
        
        for w in selected_words:
            w_clean = w.lower().strip()
            if w_clean in word_map:
                item = word_map[w_clean]
                if item["id"] not in used_ids and added_count < target_count:
                    final_batch.append(item)
                    used_ids.add(item["id"])
                    added_count += 1

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
    """Replace one word with another unused word of the SAME pos_type, excluding all words in current batch."""
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
    """Returns a dictionary mapping every inflected form to its headword."""
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


CORE_EXEMPT_WORDS: Set[str] = {
    "i", "me", "my", "myself", "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself", "she", "her", "hers", "herself",
    "it", "its", "itself", "we", "us", "our", "ours", "ourselves",
    "they", "them", "their", "theirs", "themselves",
    "this", "that", "these", "those", "who", "whom", "whose", "which", "what", "whatever", "whoever",
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
    """Return list of content words previously used (usage_count > 0)."""
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
