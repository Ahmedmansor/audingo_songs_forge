"""
word_repository.py — Repository for NGSL words, extra words, batch pulling, and vocab analytics.
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import pandas as pd
from data.database.connection import get_connection, DB_PATH
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import pandas as pd
from data.database.connection import get_connection, DB_PATH
from constants import DOMAINS

logger = logging.getLogger("audingo.word_repository")


def get_all_ngsl_words(db_path: Path = DB_PATH) -> pd.DataFrame:
    """Retrieve all NGSL words as a pandas DataFrame with COCA domain mapping."""
    with get_connection(db_path) as conn:
        df = pd.read_sql_query(
            """
            SELECT 
                id, 
                word, 
                COALESCE(domain_coca, 'Basic / Neutral') as domain, 
                domain_coca,
                coca_top_pct,
                pos_type, 
                usage_count, 
                lemma_family 
            FROM ngsl_words 
            ORDER BY word ASC
            """,
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
    """Return count of words in each COCA domain (unclassified words fall back to Basic / Neutral)."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(domain_coca, 'Basic / Neutral') as dom, COUNT(*) 
            FROM ngsl_words 
            GROUP BY dom
        """)
        return {row[0]: row[1] for row in cursor.fetchall()}


def get_domain_detailed_stats(db_path: Path = DB_PATH) -> Dict[str, Dict[str, Any]]:
    """Return detailed statistics per COCA domain: total, used, unused, percent_used, and song_count."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COALESCE(domain_coca, 'Basic / Neutral') as dom,
                COUNT(*) as total,
                SUM(CASE WHEN usage_count > 0 THEN 1 ELSE 0 END) as used,
                SUM(CASE WHEN usage_count = 0 THEN 1 ELSE 0 END) as unused
            FROM ngsl_words 
            GROUP BY dom
        """)
        rows = cursor.fetchall()

        song_counts = {}
        try:
            cursor.execute("""
                SELECT
                    TRIM(source_domain) as dom,
                    COUNT(*) as song_count
                FROM songs
                WHERE source_domain IS NOT NULL AND TRIM(source_domain) != ''
                GROUP BY dom
            """)
            song_counts = {r["dom"]: r["song_count"] for r in cursor.fetchall() if r["dom"]}
        except Exception:
            pass

        result = {}
        for r in rows:
            dom = r["dom"]
            tot = r["total"] or 0
            usd = r["used"] or 0
            uns = r["unused"] or 0
            pct_used = (usd / tot * 100) if tot > 0 else 0.0
            result[dom] = {
                "total": tot,
                "used": usd,
                "unused": uns,
                "percent_used": round(pct_used, 1),
                "song_count": song_counts.get(dom, 0),
            }
        
        # Ensure all defined domains exist in result dict
        for d in DOMAINS:
            if d not in result:
                result[d] = {
                    "total": 0,
                    "used": 0,
                    "unused": 0,
                    "percent_used": 0.0,
                    "song_count": song_counts.get(d, 0),
                }
                
        return result


def get_domain_pos_remaining_stats(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Return remaining (unused) word breakdown per domain by POS: Nouns, Verbs, Adjectives, Adverbs, Exempt, Total."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(domain_coca, 'Basic / Neutral') as dom, pos_type, word
            FROM ngsl_words
            WHERE usage_count = 0
        """)
        rows = cursor.fetchall()

        domain_dict = {
            d: {
                "domain": d,
                "nouns": 0,
                "verbs": 0,
                "adjectives": 0,
                "adverbs": 0,
                "exempt": 0,
                "total": 0,
            }
            for d in DOMAINS
        }

        for r in rows:
            dom = r["dom"]
            if dom not in domain_dict:
                dom = "Basic / Neutral"
            pos = r["pos_type"]
            w = r["word"].lower().strip()

            if pos == "Noun":
                domain_dict[dom]["nouns"] += 1
            elif pos == "Verb":
                domain_dict[dom]["verbs"] += 1
            elif pos == "Adjective":
                domain_dict[dom]["adjectives"] += 1
            elif pos == "Other":
                if w in CORE_EXEMPT_WORDS:
                    domain_dict[dom]["exempt"] += 1
                else:
                    domain_dict[dom]["adverbs"] += 1
            domain_dict[dom]["total"] += 1

        return list(domain_dict.values())


def get_words_domains(words: List[str], db_path: Path = DB_PATH) -> Dict[str, str]:
    """Bulk lookup COCA domain for a list of words."""
    if not words:
        return {}
    cleaned = list({w.strip().lower() for w in words if w.strip()})
    if not cleaned:
        return {}
    placeholders = ",".join("?" * len(cleaned))
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT word, COALESCE(domain_coca, 'Basic / Neutral') as domain FROM ngsl_words WHERE LOWER(word) IN ({placeholders})",
            cleaned
        )
        return {row["word"].lower(): (row["domain"] or "Basic / Neutral") for row in cursor.fetchall()}


def compute_domain_breakdown(words: List[str], db_path: Path = DB_PATH) -> Dict[str, Any]:
    """Given a list of words, computes the percentage and count distribution across the 6 COCA domains."""
    domain_map = get_words_domains(words, db_path=db_path)

    breakdown = {
        d: {"count": 0, "percent": 0.0, "words": []} for d in DOMAINS
    }

    classified_count = 0
    for w in words:
        w_clean = w.strip().lower()
        dom = domain_map.get(w_clean, "Basic / Neutral")
        if dom not in breakdown:
            dom = "Basic / Neutral"
        breakdown[dom]["count"] += 1
        breakdown[dom]["words"].append(w.strip())
        classified_count += 1

    # Determine primary domain:
    # Basic / Neutral is the background canvas (common functional/connective words).
    # The true thematic identity of a song is determined by the highest specialized domain!
    specialized_domains = [d for d in DOMAINS if d != "Basic / Neutral"]
    primary_domain = "Basic / Neutral"
    max_pct = 0.0

    for d in specialized_domains:
        data = breakdown[d]
        pct = round((data["count"] / classified_count * 100), 1) if classified_count > 0 else 0.0
        data["percent"] = pct
        if pct > max_pct:
            max_pct = pct
            primary_domain = d

    # Calculate Basic / Neutral percentage for the breakdown bar
    neutral_data = breakdown.get("Basic / Neutral", {"count": 0, "percent": 0.0, "words": []})
    neutral_pct = round((neutral_data["count"] / classified_count * 100), 1) if classified_count > 0 else 0.0
    neutral_data["percent"] = neutral_pct
    
    # Only if there are ZERO specialized words does the song become Basic / Neutral
    if max_pct == 0.0:
        primary_domain = "Basic / Neutral"
        max_pct = neutral_pct

    formal_pct = breakdown.get("Business & Career", {}).get("percent", 0.0) + \
                 breakdown.get("Law, Politics & Society", {}).get("percent", 0.0) + \
                 breakdown.get("Science, Tech & Academia", {}).get("percent", 0.0)
    is_high_formal = formal_pct >= 30.0

    return {
        "total_words": classified_count,
        "domains": breakdown,
        "primary_domain": primary_domain,
        "primary_percent": max_pct,
        "is_high_formal": is_high_formal,
        "formal_percent": round(formal_pct, 1)
    }


def calculate_domain_pos_quotas(
    domain: Optional[str] = None,
    blend_joker: bool = True,
    db_path: Path = DB_PATH,
    total_words: int = 20
) -> Dict[str, int]:
    """
    Dynamically calculate POS target counts (Nouns, Verbs, Modifiers) for a 20-word batch.
    - Adapts when a domain or corpus runs low on Nouns or Adjectives.
    - Modifiers pool includes Adjectives and non-exempt Adverbs.
    - If Nouns < 10, redistributes deficit to Verbs and Modifiers.
    - Guarantees the sum of quotas equals total_words (20) without leaking to unauthorized domains.
    """
    use_domain = domain if (domain and domain != "All Domains" and "الكل" not in domain and "All" not in domain) else None
    is_pure_neutral = (use_domain == "Basic / Neutral")

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if use_domain is None:
            dom_sql = ""
            params = []
        elif is_pure_neutral:
            dom_sql = "AND (domain_coca = 'Basic / Neutral' OR domain_coca IS NULL)"
            params = []
        elif blend_joker:
            dom_sql = "AND (domain_coca = ? OR domain_coca = 'Basic / Neutral' OR domain_coca IS NULL)"
            params = [use_domain]
        else:
            dom_sql = "AND domain_coca = ?"
            params = [use_domain]

        cursor.execute(f"""
            SELECT pos_type, word
            FROM ngsl_words
            WHERE usage_count = 0 {dom_sql}
        """, params)
        rows = cursor.fetchall()

    avail_nouns = 0
    avail_verbs = 0
    avail_adjs = 0
    avail_advs = 0

    for r in rows:
        pos = r["pos_type"]
        w = r["word"].lower().strip()
        if pos == "Noun":
            avail_nouns += 1
        elif pos == "Verb":
            avail_verbs += 1
        elif pos == "Adjective":
            avail_adjs += 1
        elif pos == "Other" and w not in CORE_EXEMPT_WORDS:
            avail_advs += 1

    total_avail = avail_nouns + avail_verbs + avail_adjs + avail_advs
    if total_avail == 0:
        return {"Noun": 0, "Verb": 0, "Modifier": 0, "Adjective": 0}

    # Dynamic POS balance & Adverb Absorption:
    # Baseline standard target: 10 Nouns, 5 Verbs, 5 Modifiers (when all available)
    # When nouns are low or 0 (e.g. Emotions or Basic), we dynamically distribute the noun deficit
    # between Verbs and Modifiers (Adverbs) so that Adverbs are steadily cleared (up to 6-7 per song)
    # and don't end up stranded at the end of the roadmap.
    avail_modifiers = avail_adjs + avail_advs
    base_nouns = 10

    target_nouns = min(base_nouns, avail_nouns)
    noun_deficit = base_nouns - target_nouns

    # Proportional modifier target:
    # If 0-2 nouns: target 7 modifiers (e.g. 0 Nouns + 13 Verbs + 7 Modifiers = 20)
    # If 3-6 nouns: target 6 modifiers (e.g. 4 Nouns + 10 Verbs + 6 Modifiers = 20)
    # If 7-10 nouns: target 5 modifiers (e.g. 10 Nouns + 5 Verbs + 5 Modifiers = 20)
    if noun_deficit >= 8:
        desired_modifiers = 7
    elif noun_deficit >= 4:
        desired_modifiers = 6
    else:
        desired_modifiers = 5

    target_modifiers = min(desired_modifiers, avail_modifiers)

    # Remaining slots allocated to Verbs
    target_verbs = total_words - target_nouns - target_modifiers
    if target_verbs > avail_verbs:
        target_verbs = avail_verbs

    # Balance any remaining difference to sum to total_words
    current_sum = target_nouns + target_verbs + target_modifiers
    diff = total_words - current_sum

    if diff > 0:
        extra_verbs = min(diff, max(0, avail_verbs - target_verbs))
        target_verbs += extra_verbs
        diff -= extra_verbs

        if diff > 0:
            extra_mod = min(diff, max(0, avail_modifiers - target_modifiers))
            target_modifiers += extra_mod
            diff -= extra_mod

        if diff > 0:
            extra_nouns = min(diff, max(0, avail_nouns - target_nouns))
            target_nouns += extra_nouns
            diff -= extra_nouns

    return {
        "Noun": target_nouns,
        "Verb": target_verbs,
        "Modifier": target_modifiers,
        "Adjective": target_modifiers  # alias for backwards compatibility
    }


def pull_20_words(
    domain: Optional[str] = None,
    blend_joker: bool = True,
    db_path: Path = DB_PATH
) -> List[Dict[str, Any]]:
    """
    Select 20 unused words (usage_count = 0) with dynamic POS adaptation.
    Baseline ratio: 10 Nouns, 6 Verbs, 4 Modifiers (Adjectives / Adverbs).
    
    Dynamic POS Balancing:
    - If Nouns or Adjectives in the authorized pool are low/zero, quota is dynamically redistributed
      to Verbs and Adverbs within the authorized domain(s).
    - Prevents domain leakage completely: never draws words outside target domain / Joker.
    
    Joker Blending Logic:
    - If blend_joker=True: draws 50% from Target Domain + 50% from Basic / Neutral (Joker).
    - If blend_joker=False: draws 100% from Target Domain.
    - If Basic / Neutral is chosen, draws 100% from Basic / Neutral.
    - If All Domains or None, draws randomly across the entire corpus.
    """
    quotas = calculate_domain_pos_quotas(domain, blend_joker=blend_joker, db_path=db_path, total_words=20)
    target_nouns = quotas["Noun"]
    target_verbs = quotas["Verb"]
    target_modifiers = quotas["Modifier"]

    use_domain = domain if (domain and domain != "All Domains" and "الكل" not in domain and "All" not in domain) else None
    is_pure_neutral = (use_domain == "Basic / Neutral")
    
    selected_words: List[Dict[str, Any]] = []
    used_ids: Set[int] = set()

    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        def _draw_pos(pos: str, count: int, is_modifier: bool = False):
            if count <= 0:
                return

            exempt_placeholders = ",".join("?" * len(CORE_EXEMPT_WORDS))

            def _query_words(dom_condition: str, dom_params: list, needed: int) -> List[Dict[str, Any]]:
                if needed <= 0:
                    return []
                id_clause = f"AND id NOT IN ({','.join('?' * len(used_ids))})" if used_ids else ""
                id_params = list(used_ids) if used_ids else []

                if not is_modifier:
                    q = f"""
                        SELECT id, word, lemma_family, pos_type, usage_count, COALESCE(domain_coca, 'Basic / Neutral') as domain
                        FROM ngsl_words
                        WHERE usage_count = 0 AND pos_type = ? {dom_condition} {id_clause}
                        ORDER BY RANDOM()
                        LIMIT ?
                    """
                    cursor.execute(q, [pos] + dom_params + id_params + [needed])
                    return [dict(r) for r in cursor.fetchall()]
                else:
                    # Modifier: first try Adjectives
                    q_adj = f"""
                        SELECT id, word, lemma_family, pos_type, usage_count, COALESCE(domain_coca, 'Basic / Neutral') as domain
                        FROM ngsl_words
                        WHERE usage_count = 0 AND pos_type = 'Adjective' {dom_condition} {id_clause}
                        ORDER BY RANDOM()
                        LIMIT ?
                    """
                    cursor.execute(q_adj, dom_params + id_params + [needed])
                    drawn = [dict(r) for r in cursor.fetchall()]
                    if len(drawn) < needed:
                        still_needed = needed - len(drawn)
                        temp_used = used_ids.union({w["id"] for w in drawn})
                        id_clause_adv = f"AND id NOT IN ({','.join('?' * len(temp_used))})" if temp_used else ""
                        id_params_adv = list(temp_used) if temp_used else []
                        q_adv = f"""
                            SELECT id, word, lemma_family, pos_type, usage_count, COALESCE(domain_coca, 'Basic / Neutral') as domain
                            FROM ngsl_words
                            WHERE usage_count = 0 AND pos_type = 'Other' AND LOWER(word) NOT IN ({exempt_placeholders}) {dom_condition} {id_clause_adv}
                            ORDER BY RANDOM()
                            LIMIT ?
                        """
                        cursor.execute(q_adv, list(CORE_EXEMPT_WORDS) + dom_params + id_params_adv + [still_needed])
                        drawn.extend([dict(r) for r in cursor.fetchall()])
                    return drawn

            if use_domain is None:
                # All domains
                rows = _query_words("", [], count)
                for r in rows:
                    selected_words.append(r)
                    used_ids.add(r["id"])
            elif is_pure_neutral:
                # Basic / Neutral
                rows = _query_words("AND (domain_coca = 'Basic / Neutral' OR domain_coca IS NULL)", [], count)
                for r in rows:
                    selected_words.append(r)
                    used_ids.add(r["id"])
            else:
                # Specialized domain with optional Joker blend
                if blend_joker:
                    target_quota = count // 2
                    joker_quota = count - target_quota
                else:
                    target_quota = count
                    joker_quota = 0

                # 1. Pull from target domain
                target_rows = _query_words("AND domain_coca = ?", [use_domain], target_quota)
                for r in target_rows:
                    selected_words.append(r)
                    used_ids.add(r["id"])

                # 2. Check shortage & pull Joker
                shortage = target_quota - len(target_rows)
                needed_joker = joker_quota + shortage
                if needed_joker > 0:
                    joker_rows = _query_words("AND (domain_coca = 'Basic / Neutral' OR domain_coca IS NULL)", [], needed_joker)
                    for r in joker_rows:
                        selected_words.append(r)
                        used_ids.add(r["id"])

                    # If Joker was short, compensate back from target domain
                    joker_shortage = needed_joker - len(joker_rows)
                    if joker_shortage > 0:
                        extra_target = _query_words("AND domain_coca = ?", [use_domain], joker_shortage)
                        for r in extra_target:
                            selected_words.append(r)
                            used_ids.add(r["id"])

        # Draw Nouns, Verbs, Modifiers
        _draw_pos("Noun", target_nouns, is_modifier=False)
        _draw_pos("Verb", target_verbs, is_modifier=False)
        _draw_pos("Modifier", target_modifiers, is_modifier=True)

        # Safety fill up to 20 words strictly within authorized domains
        if len(selected_words) < 20:
            still_needed = 20 - len(selected_words)
            id_clause = f"AND id NOT IN ({','.join('?' * len(used_ids))})" if used_ids else ""
            id_params = list(used_ids) if used_ids else []

            if use_domain is None:
                dom_clause = ""
                dom_params = []
            elif is_pure_neutral:
                dom_clause = "AND (domain_coca = 'Basic / Neutral' OR domain_coca IS NULL)"
                dom_params = []
            elif blend_joker:
                dom_clause = "AND (domain_coca = ? OR domain_coca = 'Basic / Neutral' OR domain_coca IS NULL)"
                dom_params = [use_domain]
            else:
                dom_clause = "AND domain_coca = ?"
                dom_params = [use_domain]

            q_fill = f"""
                SELECT id, word, lemma_family, pos_type, usage_count, COALESCE(domain_coca, 'Basic / Neutral') as domain
                FROM ngsl_words
                WHERE usage_count = 0 {dom_clause} {id_clause}
                ORDER BY RANDOM()
                LIMIT ?
            """
            cursor.execute(q_fill, dom_params + id_params + [still_needed])
            for r in cursor.fetchall():
                selected_words.append(dict(r))
                used_ids.add(r["id"])

    return selected_words


def pull_candidate_pool_for_thematic_curation(
    nouns_limit: int = 70,
    verbs_limit: int = 40,
    adjs_limit: int = 30,
    domain: Optional[str] = None,
    blend_joker: bool = True,
    db_path: Path = DB_PATH
) -> Dict[str, Any]:
    """
    Select candidate pool of unused words (usage_count = 0) for thematic AI curation.
    - Dynamically calculates target quotas so songs adapt to available inventory without cross-domain leakage.
    - Incorporates Adverbs (non-exempt Other) alongside/in place of Adjectives when depleted.
    - Strictly restricts candidate selection to authorized domain(s) (Domain + Joker if blend_joker=True).
    - Returns candidate pool dict with "Noun", "Verb", "Adjective", "Modifier", and "quotas".
    """
    quotas = calculate_domain_pos_quotas(domain, blend_joker=blend_joker, db_path=db_path, total_words=20)
    use_domain = domain if (domain and domain != "All Domains" and "الكل" not in domain and "All" not in domain) else None
    is_pure_neutral = (use_domain == "Basic / Neutral")

    pool: Dict[str, Any] = {
        "Noun": [],
        "Verb": [],
        "Adjective": [],
        "Modifier": [],
        "quotas": quotas
    }

    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        def _pull_candidates_for_pos(pos: str, count: int) -> List[Dict[str, Any]]:
            if count <= 0:
                return []
            if use_domain is None:
                cursor.execute("""
                    SELECT id, word, lemma_family, pos_type, usage_count, COALESCE(domain_coca, 'Basic / Neutral') as domain
                    FROM ngsl_words
                    WHERE usage_count = 0 AND pos_type = ?
                    ORDER BY RANDOM()
                    LIMIT ?
                """, (pos, count))
                return [dict(r) for r in cursor.fetchall()]
            elif is_pure_neutral:
                cursor.execute("""
                    SELECT id, word, lemma_family, pos_type, usage_count, COALESCE(domain_coca, 'Basic / Neutral') as domain
                    FROM ngsl_words
                    WHERE usage_count = 0 AND pos_type = ? AND (domain_coca = 'Basic / Neutral' OR domain_coca IS NULL)
                    ORDER BY RANDOM()
                    LIMIT ?
                """, (pos, count))
                return [dict(r) for r in cursor.fetchall()]
            else:
                if blend_joker:
                    target_share = count // 2
                    joker_share = count - target_share
                else:
                    target_share = count
                    joker_share = 0

                cursor.execute("""
                    SELECT id, word, lemma_family, pos_type, usage_count, COALESCE(domain_coca, 'Basic / Neutral') as domain
                    FROM ngsl_words
                    WHERE usage_count = 0 AND pos_type = ? AND domain_coca = ?
                    ORDER BY RANDOM()
                    LIMIT ?
                """, (pos, use_domain, target_share))
                target_rows = [dict(r) for r in cursor.fetchall()]

                shortage = max(0, target_share - len(target_rows))
                needed_joker = joker_share + shortage if blend_joker else 0

                joker_rows = []
                if needed_joker > 0:
                    existing_ids = [w["id"] for w in target_rows]
                    id_clause = f"AND id NOT IN ({','.join('?' * len(existing_ids))})" if existing_ids else ""
                    params = [pos] + existing_ids + [needed_joker] if existing_ids else [pos, needed_joker]
                    cursor.execute(f"""
                        SELECT id, word, lemma_family, pos_type, usage_count, COALESCE(domain_coca, 'Basic / Neutral') as domain
                        FROM ngsl_words
                        WHERE usage_count = 0 AND pos_type = ? AND (domain_coca = 'Basic / Neutral' OR domain_coca IS NULL) {id_clause}
                        ORDER BY RANDOM()
                        LIMIT ?
                    """, params)
                    joker_rows = [dict(r) for r in cursor.fetchall()]

                return target_rows + joker_rows

        # 1. Nouns
        pool["Noun"] = _pull_candidates_for_pos("Noun", nouns_limit)

        # 2. Verbs
        pool["Verb"] = _pull_candidates_for_pos("Verb", verbs_limit)

        # 3. Modifiers (Adjectives + non-exempt Adverbs)
        adj_candidates = _pull_candidates_for_pos("Adjective", adjs_limit)
        modifier_candidates = list(adj_candidates)

        adv_needed = adjs_limit - len(modifier_candidates)
        if adv_needed > 0:
            existing_ids = [w["id"] for w in modifier_candidates]
            id_clause = f"AND id NOT IN ({','.join('?' * len(existing_ids))})" if existing_ids else ""
            exempt_placeholders = ",".join("?" * len(CORE_EXEMPT_WORDS))

            if use_domain is None:
                cursor.execute(f"""
                    SELECT id, word, lemma_family, pos_type, usage_count, COALESCE(domain_coca, 'Basic / Neutral') as domain
                    FROM ngsl_words
                    WHERE usage_count = 0 AND pos_type = 'Other' AND LOWER(word) NOT IN ({exempt_placeholders}) {id_clause}
                    ORDER BY RANDOM()
                    LIMIT ?
                """, list(CORE_EXEMPT_WORDS) + existing_ids + [adv_needed] if existing_ids else list(CORE_EXEMPT_WORDS) + [adv_needed])
                modifier_candidates.extend([dict(r) for r in cursor.fetchall()])

            elif is_pure_neutral:
                cursor.execute(f"""
                    SELECT id, word, lemma_family, pos_type, usage_count, COALESCE(domain_coca, 'Basic / Neutral') as domain
                    FROM ngsl_words
                    WHERE usage_count = 0 AND pos_type = 'Other' AND LOWER(word) NOT IN ({exempt_placeholders}) 
                      AND (domain_coca = 'Basic / Neutral' OR domain_coca IS NULL) {id_clause}
                    ORDER BY RANDOM()
                    LIMIT ?
                """, list(CORE_EXEMPT_WORDS) + existing_ids + [adv_needed] if existing_ids else list(CORE_EXEMPT_WORDS) + [adv_needed])
                modifier_candidates.extend([dict(r) for r in cursor.fetchall()])

            else:
                target_share = adv_needed // 2 if blend_joker else adv_needed
                joker_share = adv_needed - target_share if blend_joker else 0

                cursor.execute(f"""
                    SELECT id, word, lemma_family, pos_type, usage_count, COALESCE(domain_coca, 'Basic / Neutral') as domain
                    FROM ngsl_words
                    WHERE usage_count = 0 AND pos_type = 'Other' AND LOWER(word) NOT IN ({exempt_placeholders})
                      AND domain_coca = ? {id_clause}
                    ORDER BY RANDOM()
                    LIMIT ?
                """, list(CORE_EXEMPT_WORDS) + [use_domain] + existing_ids + [target_share] if existing_ids else list(CORE_EXEMPT_WORDS) + [use_domain, target_share])
                target_advs = [dict(r) for r in cursor.fetchall()]
                modifier_candidates.extend(target_advs)

                shortage = max(0, target_share - len(target_advs))
                needed_joker = joker_share + shortage if blend_joker else 0
                if needed_joker > 0:
                    curr_existing = [w["id"] for w in modifier_candidates]
                    curr_id_clause = f"AND id NOT IN ({','.join('?' * len(curr_existing))})" if curr_existing else ""
                    cursor.execute(f"""
                        SELECT id, word, lemma_family, pos_type, usage_count, COALESCE(domain_coca, 'Basic / Neutral') as domain
                        FROM ngsl_words
                        WHERE usage_count = 0 AND pos_type = 'Other' AND LOWER(word) NOT IN ({exempt_placeholders})
                          AND (domain_coca = 'Basic / Neutral' OR domain_coca IS NULL) {curr_id_clause}
                        ORDER BY RANDOM()
                        LIMIT ?
                    """, list(CORE_EXEMPT_WORDS) + curr_existing + [needed_joker] if curr_existing else list(CORE_EXEMPT_WORDS) + [needed_joker])
                    modifier_candidates.extend([dict(r) for r in cursor.fetchall()])

        pool["Adjective"] = modifier_candidates
        pool["Modifier"] = modifier_candidates

    return pool


def build_curated_batch_from_words(
    selected_nouns: List[str],
    selected_verbs: List[str],
    selected_adjs: List[str],
    candidate_pool: Dict[str, Any],
    target_counts: Optional[Dict[str, int]] = None
) -> List[Dict[str, Any]]:
    """
    Map selected word strings back to full SQLite record dicts based on target quotas.
    Guarantees a full 20-word batch strictly drawn from candidate pool candidates.
    """
    if target_counts is None:
        target_counts = candidate_pool.get("quotas", {"Noun": 10, "Verb": 6, "Modifier": 4})

    t_nouns = target_counts.get("Noun", 10)
    t_verbs = target_counts.get("Verb", 6)
    t_modifiers = target_counts.get("Modifier", target_counts.get("Adjective", 4))

    final_batch: List[Dict[str, Any]] = []
    used_ids: Set[int] = set()

    def process_pos(selected_words: List[str], pool_key: str, target_count: int):
        candidates = candidate_pool.get(pool_key, [])
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

    process_pos(selected_nouns, "Noun", t_nouns)
    process_pos(selected_verbs, "Verb", t_verbs)
    process_pos(selected_adjs, "Modifier" if "Modifier" in candidate_pool else "Adjective", t_modifiers)

    # Safety guarantee: if total words < 20 across all categories, top up from remaining candidates in pool
    if len(final_batch) < 20:
        for cat in ["Verb", "Modifier", "Adjective", "Noun"]:
            for item in candidate_pool.get(cat, []):
                if item["id"] not in used_ids and len(final_batch) < 20:
                    final_batch.append(item)
                    used_ids.add(item["id"])

    return final_batch


def _fetch_swap_candidate(
    cursor,
    pos_type: str,
    allocated_ids: set,
    domain: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Helper to fetch an unused word matching pos_type, prioritizing domain if provided with graceful fallback."""
    use_domain = domain if (domain and domain != "All Domains" and "الكل" not in domain and "All" not in domain) else None
    is_pure_neutral = (use_domain == "Basic / Neutral")

    placeholders = ",".join("?" * len(allocated_ids)) if allocated_ids else "0"
    base_exclude = f"id NOT IN ({placeholders})" if allocated_ids else "1=1"

    # POS query condition: handle Modifier/Other if pos_type in ('Other', 'Adjective')
    if pos_type in ("Other", "Adjective"):
        exempt_placeholders = ",".join("?" * len(CORE_EXEMPT_WORDS))
        pos_condition = f"(pos_type = 'Adjective' OR (pos_type = 'Other' AND LOWER(word) NOT IN ({exempt_placeholders})))"
        pos_params = list(CORE_EXEMPT_WORDS)
    else:
        pos_condition = "pos_type = ?"
        pos_params = [pos_type]

    # 1. Try target domain first if specified
    if use_domain is not None:
        if is_pure_neutral:
            dom_sql = "AND (domain_coca = 'Basic / Neutral' OR domain_coca IS NULL)"
            params = pos_params + (list(allocated_ids) if allocated_ids else [])
        else:
            dom_sql = "AND domain_coca = ?"
            params = pos_params + [use_domain] + (list(allocated_ids) if allocated_ids else [])

        query = f"""
            SELECT id, word, lemma_family, pos_type, usage_count, COALESCE(domain_coca, 'Basic / Neutral') as domain
            FROM ngsl_words
            WHERE usage_count = 0 AND {pos_condition} {dom_sql} AND {base_exclude}
            ORDER BY RANDOM()
            LIMIT 1
        """
        cursor.execute(query, params)
        row = cursor.fetchone()
        if row:
            return dict(row)

        # 2. Try Joker (Basic / Neutral) before falling back to any domain
        if not is_pure_neutral:
            joker_sql = "AND (domain_coca = 'Basic / Neutral' OR domain_coca IS NULL)"
            joker_params = pos_params + (list(allocated_ids) if allocated_ids else [])
            cursor.execute(f"""
                SELECT id, word, lemma_family, pos_type, usage_count, COALESCE(domain_coca, 'Basic / Neutral') as domain
                FROM ngsl_words
                WHERE usage_count = 0 AND {pos_condition} {joker_sql} AND {base_exclude}
                ORDER BY RANDOM()
                LIMIT 1
            """, joker_params)
            row = cursor.fetchone()
            if row:
                return dict(row)

    # 3. Fallback to any domain only if no domain specified or completely exhausted
    fallback_query = f"""
        SELECT id, word, lemma_family, pos_type, usage_count, COALESCE(domain_coca, 'Basic / Neutral') as domain
        FROM ngsl_words
        WHERE usage_count = 0 AND {pos_condition} AND {base_exclude}
        ORDER BY RANDOM()
        LIMIT 1
    """
    params = pos_params + list(allocated_ids) if allocated_ids else pos_params
    cursor.execute(fallback_query, params)
    row = cursor.fetchone()
    if row:
        return dict(row)

    return None


def swap_single_word(
    pos_type: str,
    current_word_ids: List[int],
    domain: Optional[str] = None,
    db_path: Path = DB_PATH
) -> Optional[Dict[str, Any]]:
    """Replace one word with another unused word of the SAME pos_type from target domain, excluding all words in current batch."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        return _fetch_swap_candidate(cursor, pos_type, set(current_word_ids), domain=domain)


def swap_multiple_words(
    words_to_swap: List[Dict[str, Any]],
    current_word_ids: List[int],
    domain: Optional[str] = None,
    db_path: Path = DB_PATH
) -> Dict[int, Optional[Dict[str, Any]]]:
    """
    Replace multiple words with unused words of their respective pos_types from target domain,
    ensuring no duplicate IDs are introduced across the batch or newly allocated words.
    Returns mapping of old_id -> new_word_dict (or None if unavailable).
    """
    results: Dict[int, Optional[Dict[str, Any]]] = {}
    allocated_ids = set(current_word_ids)

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        for word_item in words_to_swap:
            pos = word_item["pos_type"]
            old_id = word_item["id"]

            new_word = _fetch_swap_candidate(cursor, pos, allocated_ids, domain=domain)
            if new_word:
                results[old_id] = new_word
                allocated_ids.discard(old_id)
                allocated_ids.add(new_word["id"])
            else:
                results[old_id] = None

    return results


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
