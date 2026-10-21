"""
test_emotions_pull.py — Unit tests for pulling Emotions & Relationships with dynamic quotas and leak-free guarantees.
"""

import unittest
from pathlib import Path
import tempfile
import sqlite3
import shutil

from data.repositories.word_repository import (
    calculate_domain_pos_quotas,
    pull_candidate_pool_for_thematic_curation,
    build_curated_batch_from_words,
    pull_20_words,
    CORE_EXEMPT_WORDS
)
from data.database.connection import DB_PATH


class TestEmotionsPull(unittest.TestCase):
    def setUp(self):
        # Create an isolated temporary test database with a copy of production ngsl_words
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = Path(self.temp_dir) / "test_vocab.db"

        # Copy schema and ngsl_words from production DB into isolated test DB
        src_conn = sqlite3.connect(DB_PATH)
        dst_conn = sqlite3.connect(self.test_db)
        
        with dst_conn:
            src_conn.backup(dst_conn)
            # Ensure hermetic baseline for test words regardless of live song commits
            dst_conn.execute("UPDATE ngsl_words SET usage_count = 0 WHERE word IN ('creature', 'darkness', 'servant', 'sheep')")
            
        src_conn.close()
        dst_conn.close()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_emotions_quotas_calculation(self):
        """Emotions & Relationships with Joker should dynamically allocate 4 Nouns, 12 Verbs, 4 Modifiers = 20 total."""
        quotas = calculate_domain_pos_quotas(
            domain="Emotions & Relationships",
            blend_joker=True,
            db_path=self.test_db,
            total_words=20
        )
        self.assertEqual(quotas["Noun"], 4, "Should allocate exactly 4 Nouns (the 4 remaining in Emotions)")
        self.assertEqual(quotas["Modifier"], 6, "Should allocate 6 Modifiers to steadily absorb available Adverbs")
        self.assertEqual(quotas["Verb"], 10, "Verbs should take 10 words to reach exactly 20 total")
        self.assertEqual(quotas["Noun"] + quotas["Verb"] + quotas["Modifier"], 20, "Total quotas must sum to 20")

    def test_emotions_candidate_pool_purity(self):
        """Candidate pool for Emotions & Relationships with Joker must NEVER contain words from Science, Law, or Business."""
        pool = pull_candidate_pool_for_thematic_curation(
            nouns_limit=70,
            verbs_limit=40,
            adjs_limit=30,
            domain="Emotions & Relationships",
            blend_joker=True,
            db_path=self.test_db
        )

        allowed_domains = {"Emotions & Relationships", "Basic / Neutral"}
        
        # Nouns: exactly the 4 remaining in Emotions
        self.assertEqual(len(pool["Noun"]), 4)
        for w in pool["Noun"]:
            self.assertEqual(w["domain"], "Emotions & Relationships")
            self.assertIn(w["word"], ["creature", "darkness", "servant", "sheep"])

        # Verbs: all from allowed domains
        self.assertGreater(len(pool["Verb"]), 0)
        for w in pool["Verb"]:
            self.assertIn(w["domain"], allowed_domains, f"Leaked word: {w['word']} from {w['domain']}")

        # Modifiers: all from allowed domains
        self.assertGreater(len(pool["Modifier"]), 0)
        for w in pool["Modifier"]:
            self.assertIn(w["domain"], allowed_domains, f"Leaked word: {w['word']} from {w['domain']}")
            self.assertNotIn(w["word"].lower(), CORE_EXEMPT_WORDS)

    def test_build_curated_batch_from_words_guarantees_20(self):
        """Curated batch from AI selection must produce exactly 20 words with 0 domain leakage."""
        pool = pull_candidate_pool_for_thematic_curation(
            nouns_limit=70,
            verbs_limit=40,
            adjs_limit=30,
            domain="Emotions & Relationships",
            blend_joker=True,
            db_path=self.test_db
        )

        selected_nouns = [w["word"] for w in pool["Noun"]]  # 4 nouns
        selected_verbs = [w["word"] for w in pool["Verb"][:12]]  # 12 verbs
        selected_mods = [w["word"] for w in pool["Modifier"][:4]]  # 4 modifiers

        batch = build_curated_batch_from_words(
            selected_nouns=selected_nouns,
            selected_verbs=selected_verbs,
            selected_adjs=selected_mods,
            candidate_pool=pool,
            target_counts=pool["quotas"]
        )

        self.assertEqual(len(batch), 20, "Batch must have exactly 20 words")
        allowed_domains = {"Emotions & Relationships", "Basic / Neutral"}
        for w in batch:
            self.assertIn(w["domain"], allowed_domains, f"Leaked word: {w['word']} from {w['domain']}")

        nouns = [w for w in batch if w["pos_type"] == "Noun"]
        verbs = [w for w in batch if w["pos_type"] == "Verb"]
        mods = [w for w in batch if w["pos_type"] in ("Adjective", "Other")]

        self.assertEqual(len(nouns), 4)
        self.assertEqual(len(verbs), 10)
        self.assertEqual(len(mods), 6)

    def test_random_pull_emotions_with_joker(self):
        """pull_20_words for Emotions & Relationships with blend_joker=True must yield 20 words from authorized domains only."""
        batch = pull_20_words(
            domain="Emotions & Relationships",
            blend_joker=True,
            db_path=self.test_db
        )

        self.assertEqual(len(batch), 20, "Must pull exactly 20 words")
        allowed_domains = {"Emotions & Relationships", "Basic / Neutral"}
        for w in batch:
            self.assertIn(w["domain"], allowed_domains, f"Leaked word: {w['word']} from {w['domain']}")

        nouns = [w for w in batch if w["pos_type"] == "Noun"]
        verbs = [w for w in batch if w["pos_type"] == "Verb"]
        mods = [w for w in batch if w["pos_type"] in ("Adjective", "Other")]

        self.assertEqual(len(nouns), 4)
        self.assertEqual(len(verbs), 10)
        self.assertEqual(len(mods), 6)

    def test_random_pull_pure_emotions(self):
        """pull_20_words for Emotions & Relationships with blend_joker=False must yield 20 words 100% from Emotions."""
        batch = pull_20_words(
            domain="Emotions & Relationships",
            blend_joker=False,
            db_path=self.test_db
        )

        self.assertEqual(len(batch), 20, "Must pull exactly 20 words")
        for w in batch:
            self.assertEqual(w["domain"], "Emotions & Relationships", f"Non-emotions word: {w['word']} from {w['domain']}")


if __name__ == "__main__":
    unittest.main()
