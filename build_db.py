"""
build_db.py — One-time ingestion script for NGSL vocabulary.

Reads NGSL_1.2_lemmatized_for_teaching.csv, classifies parts of speech,
and populates the SQLite ngsl_words table idempotently.
"""

import csv
import logging
from pathlib import Path
from typing import Tuple, List, Dict
import pandas as pd
import spacy

from db import init_db, get_connection

logging.basicConfig(
    filename="build_db.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filemode="w"
)
logger = logging.getLogger(__name__)

CSV_PATH = Path(__file__).parent / "NGSL_1.2_lemmatized_for_teaching.csv"


def classify_pos(headword: str, lemma_family: List[str], nlp) -> Tuple[str, bool]:
    """
    Classify the POS type of a headword into:
    - Noun
    - Verb
    - Adjective
    - Other (function words, pronouns, determiners, adverbs, prepositions)

    Returns (pos_type, is_confident).
    """
    word_lower = headword.lower().strip()
    forms_lower = [f.lower().strip() for f in lemma_family]
    
    # 1. Closed-class / function word check
    closed_class_determiners = {"a", "an", "the", "this", "that", "these", "those", "all", "each", "every", "some", "any", "no"}
    closed_class_pronouns = {"i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "their", "our", "its", "who", "whom", "whose", "which", "what", "myself", "yourself", "himself", "herself", "itself", "ourselves", "themselves"}
    closed_class_prepositions = {"about", "above", "across", "after", "against", "along", "among", "around", "at", "before", "behind", "below", "beneath", "beside", "between", "beyond", "by", "down", "during", "except", "for", "from", "in", "inside", "into", "near", "of", "off", "on", "onto", "out", "outside", "over", "past", "through", "throughout", "to", "toward", "under", "underneath", "until", "up", "upon", "with", "within", "without"}
    closed_class_conjunctions = {"and", "but", "or", "nor", "so", "yet", "for", "because", "although", "though", "while", "if", "unless", "since", "as"}
    
    if word_lower in closed_class_determiners or word_lower in closed_class_pronouns or word_lower in closed_class_prepositions or word_lower in closed_class_conjunctions:
        return "Other", True

    # 2. Clues from inflected forms in lemma_family
    has_ing = any(f.endswith("ing") and f != word_lower for f in forms_lower)
    has_ed = any((f.endswith("ed") or f.endswith("en") or f.endswith("d") or f.endswith("t")) and f != word_lower for f in forms_lower)
    has_er = any(f.endswith("er") and f != word_lower for f in forms_lower)
    has_est = any(f.endswith("est") and f != word_lower for f in forms_lower)
    
    # If it has -ing and -ed, it's virtually always a verb
    if has_ing and has_ed:
        return "Verb", True

    # If it has comparative/superlative -er and -est, it's an adjective
    if has_er and has_est:
        return "Adjective", True

    # 3. spaCy analysis
    doc = nlp(word_lower)
    token = doc[0]
    spacy_pos = token.pos_

    if spacy_pos in ("NOUN", "PROPN"):
        return "Noun", True
    elif spacy_pos in ("VERB", "AUX"):
        return "Verb", True
    elif spacy_pos == "ADJ":
        return "Adjective", True
    elif spacy_pos in ("ADV", "PRON", "DET", "ADP", "CCONJ", "SCONJ", "PART", "INTJ", "NUM"):
        return "Other", True

    # 4. Fallback default
    logger.warning("Unconfident POS for '%s' (spaCy POS: %s). Defaulting to Noun.", headword, spacy_pos)
    return "Noun", False


def ingest_ngsl(csv_path: Path = CSV_PATH) -> None:
    """Read CSV and populate ngsl_words table."""
    init_db()

    print(f"Loading spaCy model...")
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        # If not yet downloaded, download it
        from spacy.cli import download
        download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")

    print(f"Reading {csv_path}...")
    
    rows_to_insert = []
    flagged_count = 0
    pos_counts = {"Noun": 0, "Verb": 0, "Adjective": 0, "Other": 0}

    with open(csv_path, mode="r", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        
        row_index = 0
        for row in reader:
            row_index += 1
            # Skip rows 1-13 (metadata/notes)
            if row_index <= 13:
                continue

            if not row or not any(cell.strip() for cell in row):
                continue

            headword = row[0].strip()
            if not headword:
                continue

            # Extract all non-empty cells
            lemma_items = [headword]
            for cell in row[1:]:
                clean_cell = cell.strip()
                if clean_cell and clean_cell not in lemma_items:
                    lemma_items.append(clean_cell)

            lemma_family_str = ", ".join(lemma_items)

            # Classify POS
            pos_type, is_confident = classify_pos(headword, lemma_items, nlp)
            if not is_confident:
                flagged_count += 1

            pos_counts[pos_type] = pos_counts.get(pos_type, 0) + 1

            rows_to_insert.append((
                headword,
                lemma_family_str,
                pos_type,
                0  # usage_count default 0
            ))

    print(f"Parsed {len(rows_to_insert)} words. Inserting into SQLite ngsl_words...")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO ngsl_words (word, lemma_family, pos_type, usage_count)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(word) DO NOTHING
            """,
            rows_to_insert
        )
        conn.commit()

    print(" Ingestion complete!")
    print(f"Total words: {len(rows_to_insert)}")
    print(f"POS Breakdown: {pos_counts}")
    print(f"Flagged for review: {flagged_count} (logged in build_db.log)")


if __name__ == "__main__":
    ingest_ngsl()
