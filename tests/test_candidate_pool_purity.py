import unittest
from pathlib import Path
import tempfile
import sqlite3
import shutil

from data.repositories.word_repository import pull_candidate_pool_for_thematic_curation


class TestCandidatePoolPurity(unittest.TestCase):
    def setUp(self):
        # Create an isolated temporary test database to avoid touching production data
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_vocab.db"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE ngsl_words (
                id INTEGER PRIMARY KEY,
                word TEXT NOT NULL,
                lemma_family TEXT,
                pos_type TEXT,
                usage_count INTEGER DEFAULT 0,
                domain_coca TEXT
            )
        """)
        
        # Populate:
        # 15 Basic / Neutral Nouns, 10 Verbs, 5 Adjectives
        # 30 Science Nouns, 30 Verbs, 30 Adjectives
        words = []
        uid = 1
        for i in range(15):
            words.append((uid, f"neutral_noun_{i}", f"neutral_noun_{i}", "Noun", 0, "Basic / Neutral"))
            uid += 1
        for i in range(10):
            words.append((uid, f"neutral_verb_{i}", f"neutral_verb_{i}", "Verb", 0, "Basic / Neutral"))
            uid += 1
        for i in range(5):
            words.append((uid, f"neutral_adj_{i}", f"neutral_adj_{i}", "Adjective", 0, None))  # NULL is Basic / Neutral
            uid += 1

        for i in range(30):
            words.append((uid, f"sci_noun_{i}", f"sci_noun_{i}", "Noun", 0, "Science, Tech & Academia"))
            uid += 1
            words.append((uid, f"sci_verb_{i}", f"sci_verb_{i}", "Verb", 0, "Science, Tech & Academia"))
            uid += 1
            words.append((uid, f"sci_adj_{i}", f"sci_adj_{i}", "Adjective", 0, "Science, Tech & Academia"))
            uid += 1

        cursor.executemany(
            "INSERT INTO ngsl_words (id, word, lemma_family, pos_type, usage_count, domain_coca) VALUES (?,?,?,?,?,?)",
            words
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_neutral_candidate_pool_is_100_percent_pure(self):
        """When Basic / Neutral is selected, the candidate pool must never be polluted by Science words,
        even though limits (70, 40, 30) exceed available Neutral counts (15, 10, 5)."""
        pool = pull_candidate_pool_for_thematic_curation(
            nouns_limit=70,
            verbs_limit=40,
            adjs_limit=30,
            domain="Basic / Neutral",
            blend_joker=True,
            db_path=self.db_path
        )
        
        self.assertEqual(len(pool["Noun"]), 15)
        self.assertEqual(len(pool["Verb"]), 10)
        self.assertEqual(len(pool["Adjective"]), 5)
        
        for pos in ["Noun", "Verb", "Adjective"]:
            for item in pool[pos]:
                self.assertEqual(item["domain"], "Basic / Neutral", f"Word '{item['word']}' should be Basic / Neutral!")
                self.assertFalse(item["word"].startswith("sci_"), f"Word '{item['word']}' should not be a Science word!")

    def test_pure_domain_candidate_pool_is_100_percent_pure(self):
        """When a specialized domain is selected with blend_joker=False, candidate pool must be pure domain words."""
        pool = pull_candidate_pool_for_thematic_curation(
            nouns_limit=20,
            verbs_limit=15,
            adjs_limit=10,
            domain="Science, Tech & Academia",
            blend_joker=False,
            db_path=self.db_path
        )
        
        self.assertEqual(len(pool["Noun"]), 20)
        self.assertEqual(len(pool["Verb"]), 15)
        self.assertEqual(len(pool["Adjective"]), 10)
        
        for pos in ["Noun", "Verb", "Adjective"]:
            for item in pool[pos]:
                self.assertEqual(item["domain"], "Science, Tech & Academia")

    def test_fallback_when_words_below_minimum_song_requirements(self):
        """If a domain has fewer than minimum song requirements (e.g. only 2 Adjectives, while 4 needed),
        it should gracefully fall back to ensure at least 4 adjectives are available."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Delete neutral adjectives until only 2 remain
        cursor.execute("DELETE FROM ngsl_words WHERE pos_type = 'Adjective' AND (domain_coca = 'Basic / Neutral' OR domain_coca IS NULL) AND id > 27")
        conn.commit()
        conn.close()

        pool = pull_candidate_pool_for_thematic_curation(
            nouns_limit=70,
            verbs_limit=40,
            adjs_limit=30,
            domain="Basic / Neutral",
            blend_joker=True,
            db_path=self.db_path
        )
        # Should have at least 4 adjectives now via fallback
        self.assertGreaterEqual(len(pool["Adjective"]), 4)


if __name__ == "__main__":
    unittest.main()
