import unittest
from pathlib import Path
import tempfile
import sqlite3
import shutil

import db
from data.repositories.word_repository import swap_single_word, swap_multiple_words


class TestDomainAwareSwap(unittest.TestCase):
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
        # Populate sample words across domains
        sample_data = [
            (1, "quantum", "quantum", "Noun", 0, "Science, Tech & Academia"),
            (2, "particle", "particle", "Noun", 0, "Science, Tech & Academia"),
            (3, "analyze", "analyze", "Verb", 0, "Science, Tech & Academia"),
            (4, "market", "market", "Noun", 0, "Business & Career"),
            (5, "invest", "invest", "Verb", 0, "Business & Career"),
            (6, "profitable", "profitable", "Adjective", 0, "Business & Career"),
            (7, "smile", "smile", "Verb", 0, "Basic / Neutral"),
            (8, "happy", "happy", "Adjective", 0, "Basic / Neutral"),
            (9, "water", "water", "Noun", 0, None),  # NULL falls back to Basic / Neutral
        ]
        cursor.executemany(
            "INSERT INTO ngsl_words (id, word, lemma_family, pos_type, usage_count, domain_coca) VALUES (?,?,?,?,?,?)",
            sample_data
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_swap_single_word_matches_selected_domain(self):
        # Swap noun prioritizing "Science, Tech & Academia"
        res = swap_single_word("Noun", current_word_ids=[1], domain="Science, Tech & Academia", db_path=self.db_path)
        self.assertIsNotNone(res)
        self.assertEqual(res["word"], "particle")
        self.assertEqual(res["domain"], "Science, Tech & Academia")

    def test_swap_single_word_business_domain(self):
        res = swap_single_word("Verb", current_word_ids=[], domain="Business & Career", db_path=self.db_path)
        self.assertIsNotNone(res)
        self.assertEqual(res["word"], "invest")
        self.assertEqual(res["domain"], "Business & Career")

    def test_swap_multiple_words_matches_selected_domain(self):
        words_to_swap = [
            {"id": 100, "word": "dummy1", "pos_type": "Noun"},
            {"id": 101, "word": "dummy2", "pos_type": "Verb"},
        ]
        res = swap_multiple_words(words_to_swap, current_word_ids=[1], domain="Science, Tech & Academia", db_path=self.db_path)
        self.assertEqual(res[100]["word"], "particle")
        self.assertEqual(res[100]["domain"], "Science, Tech & Academia")
        self.assertEqual(res[101]["word"], "analyze")
        self.assertEqual(res[101]["domain"], "Science, Tech & Academia")

    def test_swap_fallback_when_domain_exhausted(self):
        # Science has only 1 verb: "analyze" (id=3). If id=3 is already in batch, it falls back to another domain
        res = swap_single_word("Verb", current_word_ids=[3], domain="Science, Tech & Academia", db_path=self.db_path)
        self.assertIsNotNone(res)
        self.assertIn(res["word"], ["invest", "smile"])

    def test_swap_all_domains(self):
        res = swap_single_word("Noun", current_word_ids=[], domain="All Domains", db_path=self.db_path)
        self.assertIsNotNone(res)
        self.assertIn(res["word"], ["quantum", "particle", "market", "water"])
