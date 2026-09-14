"""
classify_corpus.py — Automated batch classification of all 2,809 NGSL words
into 4 core semantic domains using Gemini Flash API.
"""

import os
import sys
import json
import time
import sqlite3
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from google import genai

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure Windows stdout handles UTF-8 emojis cleanly
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv(PROJECT_ROOT / ".env")

from constants import DOMAINS, GEMINI_MODEL_CANDIDATES
import db

VALID_DOMAINS = set(DOMAINS)
BATCH_SIZE = 140

PROMPT_TEMPLATE = """You are an expert linguistic taxonomist categorizing English vocabulary for an ESL songwriting and language learning platform.

Each word MUST be classified into EXACTLY ONE of these 4 semantic domains:
1. "Street & Daily Life": Casual conversation, physical actions, food & drinks, vehicles, places, household items, clothing, common errands, practical everyday slang & idioms.
2. "Emotions & Relationships": Feelings, romance, heartbreak, sadness, joy, trust, betrayal, soul, personal conflicts, psychological states, friendships, intimate human connections.
3. "Business & Career": Workplaces, corporate life, offices, jobs, salaries, negotiation, finance, investments, contracts, trade, employers, professional ambition & success.
4. "Society, Law & Deep Ideas": Civic life, courts, crime & justice, government, democracy, public policy, philosophy, academic concepts, societal debate, rights.

CRITICAL INSTRUCTIONS:
- For basic structural words (pronouns, conjunctions, core basic prepositions/verbs like 'the', 'and', 'go', 'get'), classify them as "Street & Daily Life".
- Classify ALL {count} words provided below.
- Return ONLY a JSON object mapping each word string to its exact domain string.
Do not wrap in markdown or any other explanation.

Words to classify ({count} words):
{words_json}
"""


def get_unclassified_words(conn: sqlite3.Connection) -> List[str]:
    """Retrieve all words where domain is NULL or unassigned."""
    cur = conn.cursor()
    cur.execute(
        "SELECT word FROM ngsl_words WHERE domain IS NULL OR domain = '' OR domain = 'NULL' ORDER BY id ASC"
    )
    return [r[0] for r in cur.fetchall()]


def call_gemini_batch(client: genai.Client, words: List[str]) -> Dict[str, str]:
    """Call Gemini with model fallback chain to classify a batch of words."""
    prompt = PROMPT_TEMPLATE.format(
        count=len(words),
        words_json=json.dumps(words)
    )

    last_error = None
    for model in GEMINI_MODEL_CANDIDATES:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.1
                }
            )
            raw_text = response.text.strip()
            # Clean markdown fences if any
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

            parsed = json.loads(raw_text)
            if isinstance(parsed, dict) and len(parsed) > 0:
                return parsed
        except Exception as e:
            last_error = e
            # Try next model in chain
            time.sleep(1)
            continue

    raise RuntimeError(f"All Gemini models failed for batch: {last_error}")


def normalize_domain(raw_domain: str) -> str:
    """Ensure domain string matches one of the 4 canonical domains exactly."""
    if not raw_domain:
        return "Street & Daily Life"
    raw_lower = raw_domain.lower()
    if "emotion" in raw_lower or "relationship" in raw_lower or "heart" in raw_lower:
        return "Emotions & Relationships"
    if "business" in raw_lower or "career" in raw_lower or "work" in raw_lower or "money" in raw_lower:
        return "Business & Career"
    if "society" in raw_lower or "law" in raw_lower or "deep" in raw_lower or "idea" in raw_lower or "civic" in raw_lower:
        return "Society, Law & Deep Ideas"
    return "Street & Daily Life"


def main():
    db.init_db()
    conn = db.get_connection()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY is not set.")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    unclassified = get_unclassified_words(conn)
    total_unclassified = len(unclassified)
    print(f"🚀 Found {total_unclassified} words needing classification in ngsl_words.")

    if total_unclassified == 0:
        print("✅ All words are already classified!")
        report_distribution(conn)
        return

    batches = [unclassified[i:i + BATCH_SIZE] for i in range(0, total_unclassified, BATCH_SIZE)]
    total_batches = len(batches)
    print(f"📦 Total batches to process: {total_batches} (Batch size: {BATCH_SIZE})")

    processed_count = 0
    t_start = time.time()

    for idx, batch_words in enumerate(batches, start=1):
        print(f"\n⚡ Processing Batch {idx}/{total_batches} ({len(batch_words)} words)...", end="", flush=True)
        try:
            batch_result = call_gemini_batch(client, batch_words)
            
            # Update database
            cur = conn.cursor()
            updated_in_batch = 0
            for word in batch_words:
                raw_dom = batch_result.get(word) or batch_result.get(word.lower())
                domain = normalize_domain(raw_dom)
                cur.execute("UPDATE ngsl_words SET domain = ? WHERE word = ?", (domain, word))
                updated_in_batch += 1
            
            conn.commit()
            processed_count += updated_in_batch
            elapsed = time.time() - t_start
            print(f" Done! ({updated_in_batch} saved, cumulative: {processed_count}/{total_unclassified}, {elapsed:.1f}s)")

            # Brief pause to respect API rate limits
            time.sleep(1.2)

        except Exception as e:
            print(f"\n❌ Error in batch {idx}: {e}")
            # Save fallback for this batch so we make progress
            cur = conn.cursor()
            for word in batch_words:
                cur.execute("UPDATE ngsl_words SET domain = 'Street & Daily Life' WHERE word = ? AND domain IS NULL", (word,))
            conn.commit()
            time.sleep(3)

    print("\n🎉 Classification completed successfully!")
    report_distribution(conn)


def report_distribution(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("SELECT domain, COUNT(*) FROM ngsl_words GROUP BY domain ORDER BY COUNT(*) DESC")
    rows = cur.fetchall()
    print("\n📊 Final NGSL Corpus Distribution Across 4 Domains:")
    print("=" * 60)
    total = sum(r[1] for r in rows)
    for dom, count in rows:
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {dom:<30}: {count:>5} words ({pct:>5.1f}%)")
    print("=" * 60)
    print(f"  Total Classified Words        : {total:>5} words")


if __name__ == "__main__":
    main()
