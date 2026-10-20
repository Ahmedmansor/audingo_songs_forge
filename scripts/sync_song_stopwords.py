"""
sync_song_stopwords.py — One-time sync script to credit grammatical function words
and stopwords that appeared in existing approved songs.
"""

import sys
import shutil
import sqlite3
import datetime
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from data.database.connection import DB_PATH
from data.repositories.word_repository import get_all_lemma_mappings, CORE_EXEMPT_WORDS
from domain.services.lyrics_service import clean_lyrics_text
import spacy


def main():
    print("=" * 60)
    print("Step 1: Creating safety backup of ngsl_vocab.db...")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = ROOT_DIR / f"ngsl_vocab.db.backup_{timestamp}"
    shutil.copy2(DB_PATH, backup_path)
    print(f"Safety backup created at: {backup_path.name}")

    print("\nStep 2: Loading spaCy and lemma mappings...")
    nlp = spacy.load("en_core_web_sm")
    lemma_map = get_all_lemma_mappings(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Query all songs
    cursor.execute("SELECT id, title, lyrics FROM songs ORDER BY id ASC")
    songs = cursor.fetchall()
    print(f"Total songs to scan: {len(songs)}")

    # Target words: pos_type = 'Other' with usage_count = 0
    cursor.execute("SELECT word, domain_coca FROM ngsl_words WHERE pos_type = 'Other' AND usage_count = 0")
    target_rows = cursor.fetchall()
    target_zero_words = {r[0].lower().strip(): (r[1] or "Basic / Neutral") for r in target_rows}
    print(f"Total candidate 'Other' words with 0 usage: {len(target_zero_words)}")

    # Track how many songs each word appeared in
    word_song_occurrences = {w: 0 for w in target_zero_words}

    print("\nStep 3: Scanning songs lyrics...")
    for song_id, title, lyrics in songs:
        if not lyrics:
            continue
        cleaned = clean_lyrics_text(lyrics)
        doc = nlp(cleaned.lower())
        seen_in_this_song = set()
        for token in doc:
            w_raw = token.text.strip().lower()
            w_lemma = token.lemma_.strip().lower()
            hw = lemma_map.get(w_lemma) or lemma_map.get(w_raw)
            if w_raw in target_zero_words:
                seen_in_this_song.add(w_raw)
            if w_lemma in target_zero_words:
                seen_in_this_song.add(w_lemma)
            if hw in target_zero_words:
                seen_in_this_song.add(hw)

        for w in seen_in_this_song:
            word_song_occurrences[w] += 1

    words_to_update = {w: count for w, count in word_song_occurrences.items() if count > 0}
    print(f"\nStep 4: Found {len(words_to_update)} words present in existing songs.")

    # Execute database update inside transaction
    updated_count = 0
    with conn:
        for word, count in words_to_update.items():
            cursor.execute(
                "UPDATE ngsl_words SET usage_count = usage_count + ? WHERE LOWER(word) = ?",
                (count, word)
            )
            updated_count += 1

    print(f"Successfully updated usage_count for {updated_count} words in ngsl_words!")

    # Verify new totals
    cursor.execute("SELECT COUNT(*) FROM ngsl_words WHERE usage_count > 0")
    total_used = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM ngsl_words WHERE usage_count = 0")
    total_unused = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM ngsl_words WHERE COALESCE(domain_coca, 'Basic / Neutral') = 'Basic / Neutral' AND usage_count = 0")
    basic_unused = cursor.fetchone()[0]

    print("\n" + "=" * 60)
    print("SYNC COMPLETED SUCCESSFULLY:")
    print(f"Total NGSL Words Covered (usage_count > 0): {total_used:,} ({(total_used/2809)*100:.1f}%)")
    print(f"Total NGSL Words Remaining (usage_count = 0): {total_unused:,}")
    print(f"Remaining in Basic / Neutral: {basic_unused:,}")
    print("=" * 60)

    # Print top updated words
    print("\nTop updated words:")
    sorted_words = sorted(words_to_update.items(), key=lambda x: x[1], reverse=True)
    for w, c in sorted_words[:25]:
        print(f"  - '{w}': appeared in {c} songs (usage_count = {c})")

    conn.close()


if __name__ == "__main__":
    main()
