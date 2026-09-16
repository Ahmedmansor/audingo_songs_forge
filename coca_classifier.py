"""
coca_classifier.py — COCA-based Domain Classification for NGSL Vocabulary.

Reads COCA Word Frequency data (PM metrics across 6 genres) and classifies
NGSL words into 6 refined semantic domains:
  1. Street & Daily Life (spokPM + TVMPM)
  2. Emotions & Relationships (ficPM)
  3. Law, Politics & Society (newsPM)
  4. Science, Tech & Academia (acadPM)
  5. Business & Career (magPM + newsPM)
  6. Basic / Neutral (balanced, low-margin, or proper noun words)

Populates columns `domain_coca` and `coca_top_pct` in `ngsl_words` table.
The original `domain` column is preserved intact for comparison.
"""

import sys
import sqlite3
from pathlib import Path
import pandas as pd

from data.database.connection import DB_PATH, get_connection, init_db

# Configure stdout for UTF-8 output in Windows console
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
COCA_CSV_PATH = ROOT_DIR / "COCA_WordFrequency.csv"

# Configuration constants
CAPS_NOUN_THRESHOLD = 0.55  # Noun in DB + %caps > 55% -> forced Basic / Neutral
THRESH_HIGH = 0.35          # Dominance >= 35% -> High confidence
THRESH_LOW = 0.28           # Moderate band threshold
MARGIN_MID = 1.3            # Minimum margin ratio for moderate band

# Recoverable dialect/spelling mappings (BrE -> AmE)
ALIASES = {
    "autumn": "fall",
    "dialog": "dialogue",
    "whilst": "while",
}

# Manual overrides dictionary (reserved for unfixable edge cases)
MANUAL_OVERRIDES = {}


def classify_word(row: pd.Series, word: str, db_pos: str) -> tuple[str, float, float]:
    """
    Classifies a word based on normalized COCA PM frequencies.

    Returns:
        (domain_name, top_category_percentage, margin_ratio)
    """
    # 1. Manual override guard
    if word in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[word], 0.0, 0.0

    # 2. Proper noun guard: Noun in DB + high capitalization in corpus
    if db_pos == "Noun" and float(row.get("%caps", 0.0)) > CAPS_NOUN_THRESHOLD:
        return "Basic / Neutral", 0.0, 0.0

    # 3. Frequency scores across domains (zero overlap logic)
    scores = {
        "Street & Daily Life": (float(row["spokPM"]) + float(row["TVMPM"])) / 2.0,
        "Emotions & Relationships": float(row["ficPM"]),
        "Law, Politics & Society": float(row["newsPM"]),
        "Science, Tech & Academia": float(row["acadPM"]),
        "Business & Career": (float(row["magPM"]) + float(row["newsPM"])) / 2.0,
    }

    total = sum(scores.values())
    if total == 0:
        return "Basic / Neutral", 0.0, 0.0

    # 4. Normalized ratios and margin
    ratios = {cat: val / total for cat, val in scores.items()}
    sorted_cats = sorted(ratios.items(), key=lambda x: -x[1])
    max_cat, max_ratio = sorted_cats[0]
    second_ratio = sorted_cats[1][1]
    margin = max_ratio / second_ratio if second_ratio > 0 else 99.0

    # 5. Tiered decision logic
    pct = round(max_ratio * 100.0, 2)
    mrg = round(margin, 2)

    if max_ratio >= THRESH_HIGH:
        return max_cat, pct, mrg
    elif max_ratio >= THRESH_LOW and margin >= MARGIN_MID:
        return max_cat, pct, mrg
    else:
        return "Basic / Neutral", pct, mrg


def run_classification(db_path: Path = DB_PATH, coca_path: Path = COCA_CSV_PATH) -> None:
    """Executes the classification and database migration."""
    print("=" * 70)
    print("🚀 Starting COCA Domain Classification Migration")
    print("=" * 70)

    # Step 1: Ensure database schema is initialized with new columns
    print("📌 Step 1: Checking database schema...")
    init_db(db_path)

    # Step 2: Load COCA data
    print(f"📌 Step 2: Loading COCA frequency data from {coca_path.name}...")
    if not coca_path.exists():
        raise FileNotFoundError(f"COCA CSV not found at: {coca_path}")

    coca = pd.read_csv(coca_path)
    coca["lemma_clean"] = coca["lemma"].astype(str).str.strip().str.lower()
    coca_unique = coca.drop_duplicates(subset=["lemma_clean"], keep="first").set_index("lemma_clean")
    print(f"   Loaded {len(coca_unique)} unique COCA lemmas.")

    # Step 3: Load NGSL words from database
    print("📌 Step 3: Loading NGSL vocabulary from database...")
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT word, pos_type FROM ngsl_words ORDER BY id ASC")
        ngsl_rows = cursor.fetchall()

    total_words = len(ngsl_rows)
    print(f"   Found {total_words} words in ngsl_words table.")

    # Step 4: Classify all words
    print("📌 Step 4: Running classification algorithm...")
    update_records = []
    stats = {
        "classified": 0,
        "null_words": 0,
        "aliases_used": 0,
        "caps_filtered": 0,
    }
    domain_counts = {}

    for row in ngsl_rows:
        word = row["word"]
        pos = row["pos_type"]
        wl = word.lower().strip()

        lookup_word = ALIASES.get(wl, wl)
        if lookup_word != wl:
            stats["aliases_used"] += 1

        if lookup_word in coca_unique.index:
            coca_row = coca_unique.loc[lookup_word]
            dom, pct, mrg = classify_word(coca_row, wl, pos)
            update_records.append((dom, pct, word))
            stats["classified"] += 1
            domain_counts[dom] = domain_counts.get(dom, 0) + 1
            if dom == "Basic / Neutral" and pct == 0.0:
                stats["caps_filtered"] += 1
        else:
            # Word truly missing from COCA
            update_records.append((None, None, word))
            stats["null_words"] += 1
            domain_counts["NULL (Missing)"] = domain_counts.get("NULL (Missing)", 0) + 1

    # Step 5: Batch update database
    print(f"📌 Step 5: Updating {len(update_records)} records in database...")
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany(
            """
            UPDATE ngsl_words
            SET domain_coca = ?, coca_top_pct = ?
            WHERE word = ?
            """,
            update_records,
        )
        conn.commit()

    print("✅ Database update committed successfully.")

    # Step 6: Print validation summary
    print("\n" + "=" * 70)
    print("📊 MIGRATION SUMMARY & DOMAIN DISTRIBUTION")
    print("=" * 70)
    print(f"{'Domain':<32} {'Count':>8} {'Percentage':>12}")
    print("-" * 54)

    for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
        pct_str = f"{(count / total_words) * 100:.1f}%"
        print(f"{domain:<32} {count:>8} {pct_str:>12}")

    print("-" * 54)
    print(f"{'Total NGSL Words':<32} {total_words:>8} {'100.0%':>12}")
    print("\nOperational Diagnostics:")
    print(f"  • Successfully Classified: {stats['classified']} words")
    print(f"  • Proper Nouns Guarded (CAPS Filter): {stats['caps_filtered']} words")
    print(f"  • Spelling Aliases Mapped (BrE->AmE): {stats['aliases_used']} words")
    print(f"  • Unmapped (COCA NULL): {stats['null_words']} words")

    # Sample Spot Check
    print("\n🔍 Spot Check (Key Benchmark Words):")
    sample_words = [
        "time", "love", "court", "laboratory", "murder",
        "tax", "invest", "dream", "research", "police",
        "contract", "university", "autumn", "dialog", "whilst"
    ]
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in sample_words)
        cursor.execute(
            f"SELECT word, domain, domain_coca, coca_top_pct FROM ngsl_words WHERE word IN ({placeholders})",
            sample_words,
        )
        spot_rows = {r["word"]: r for r in cursor.fetchall()}

    print(f"{'Word':<14} {'Old domain':<24} {'domain_coca':<26} {'coca_top_pct':>12}")
    print("-" * 78)
    for w in sample_words:
        r = spot_rows.get(w)
        if r:
            old_d = str(r["domain"]) if r["domain"] else "NULL"
            new_d = str(r["domain_coca"]) if r["domain_coca"] else "NULL"
            pct_val = f"{r['coca_top_pct']:.1f}%" if r["coca_top_pct"] is not None else "—"
            print(f"{w:<14} {old_d:<24} {new_d:<26} {pct_val:>12}")
    print("=" * 78)


if __name__ == "__main__":
    run_classification()
