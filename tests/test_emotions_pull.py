"""
test_emotions_pull.py — Unit tests for pulling Emotions & Relationships with dynamic quotas and leak-free guarantees.
"""

import unittest
from pathlib import Path
import tempfile
import sqlite3
import shutil
from contextlib import closing

from data.repositories.word_repository import (
    calculate_domain_pos_quotas,
    pull_candidate_pool_for_thematic_curation,
    build_curated_batch_from_words,
    pull_20_words,
    CORE_EXEMPT_WORDS
)



class TestEmotionsPull(unittest.TestCase):
    def setUp(self):
        # Use a fully synthetic, isolated inventory; never connect to the production database.
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = Path(self.temp_dir) / "test_vocab.db"

        with closing(sqlite3.connect(self.test_db)) as conn, conn:
            conn.execute("CREATE TABLE ngsl_words (id INTEGER PRIMARY KEY, word TEXT, lemma_family TEXT, pos_type TEXT, usage_count INTEGER, domain_coca TEXT)")
            rows = []
            for dom, verbs, modifiers in [("Emotions & Relationships", 120, 13), ("Basic / Neutral", 129, 51), ("Business & Career", 40, 20)]:
                for pos, count in [("Verb", verbs), ("Other", modifiers)]:
                    for i in range(count):
                        word = f"{dom}_{pos}_{i}"
                        rows.append((len(rows)+1, word, word, pos, 0, dom))
            conn.executemany("INSERT INTO ngsl_words VALUES (?,?,?,?,?,?)", rows)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_emotions_quotas_calculation(self):
        """Emotions & Relationships with Joker should dynamically allocate 0 Nouns, 16 Verbs, 4 Modifiers = 20 total."""
        quotas = calculate_domain_pos_quotas(
            domain="Emotions & Relationships",
            blend_joker=True,
            db_path=self.test_db,
            total_words=20
        )
        self.assertEqual(quotas["Noun"], 0)
        self.assertEqual(quotas["Modifier"], 4)
        self.assertEqual(quotas["Verb"], 16)
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
        
        # This inventory has no unused nouns.
        self.assertEqual(len(pool["Noun"]), 0)
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

        selected_nouns = [w["word"] for w in pool["Noun"]]
        selected_verbs = [w["word"] for w in pool["Verb"][:16]]
        selected_mods = [w["word"] for w in pool["Modifier"][:4]]

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

        self.assertEqual(len(nouns), 0)
        self.assertEqual(len(verbs), 16)
        self.assertEqual(len(mods), 4)
        for dom, verbs_expected, mods_expected in [("Emotions & Relationships", 9, 1), ("Basic / Neutral", 7, 3)]:
            self.assertEqual(sum(w["domain"] == dom for w in verbs), verbs_expected)
            self.assertEqual(sum(w["domain"] == dom for w in mods), mods_expected)


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

        self.assertEqual(len(nouns), 0)
        self.assertEqual(len(verbs), 16)
        self.assertEqual(len(mods), 4)
        for dom, verbs_expected, mods_expected in [("Emotions & Relationships", 9, 1), ("Basic / Neutral", 7, 3)]:
            self.assertEqual(sum(w["domain"] == dom for w in verbs), verbs_expected)
            self.assertEqual(sum(w["domain"] == dom for w in mods), mods_expected)


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
        self.assertEqual(sum(w['pos_type'] == 'Other' for w in batch), 4)
        self.assertEqual(sum(w['pos_type'] == 'Verb' for w in batch), 16)

    def test_depleted_joker_stays_in_domain_and_rebalances(self):
        with closing(sqlite3.connect(self.test_db)) as conn, conn:
            conn.execute("UPDATE ngsl_words SET usage_count=1 WHERE domain_coca='Basic / Neutral'")
        batch = pull_20_words('Emotions & Relationships', db_path=self.test_db)
        self.assertEqual(len(batch), 20)
        self.assertEqual(sum(w['pos_type'] == 'Other' for w in batch), 4)
        self.assertEqual({w['domain'] for w in batch}, {'Emotions & Relationships'})

    def test_small_candidate_limits_still_supply_required_sources(self):
        pool = pull_candidate_pool_for_thematic_curation(0, 2, 1,
            domain='Emotions & Relationships', db_path=self.test_db)
        batch = build_curated_batch_from_words([], [], [], pool)
        self.assertEqual(len(batch), 20)
        self.assertEqual(len({w['id'] for w in batch}), 20)
        for key, source_counts in pool['domain_quotas'].items():
            for source, count in source_counts.items():
                self.assertEqual(sum(w['domain'] == source and
                    ('Modifier' if w['pos_type'] in ('Adjective', 'Other') else w['pos_type']) == key
                    for w in batch), count)

    def test_smart_pull_without_joker_keeps_four_modifiers(self):
        pool = pull_candidate_pool_for_thematic_curation(domain='Emotions & Relationships',
            blend_joker=False, db_path=self.test_db)
        self.assertEqual(pool['quotas']['Modifier'], 4)
        batch = build_curated_batch_from_words([], [], [], pool)
        self.assertEqual(len(batch), 20)
        self.assertEqual(len({w['id'] for w in batch}), 20)
        self.assertEqual(sum(w['pos_type'] == 'Other' for w in batch), 4)
        self.assertEqual({w['domain'] for w in batch}, {'Emotions & Relationships'})

    def test_actual_modifier_shortage_does_not_import_joker_words(self):
        with closing(sqlite3.connect(self.test_db)) as conn, conn:
            conn.execute("UPDATE ngsl_words SET usage_count=1 WHERE domain_coca='Emotions & Relationships' "
                         "AND pos_type='Other' AND id NOT IN "
                         "(SELECT id FROM ngsl_words WHERE domain_coca='Emotions & Relationships' AND pos_type='Other' LIMIT 2)")
        for smart in (False, True):
            if smart:
                pool = pull_candidate_pool_for_thematic_curation(domain='Emotions & Relationships',
                    blend_joker=False, db_path=self.test_db)
                batch = build_curated_batch_from_words([], [], [], pool)
            else:
                batch = pull_20_words('Emotions & Relationships', blend_joker=False, db_path=self.test_db)
            self.assertEqual(len(batch), 20)
            self.assertEqual(sum(w['pos_type'] == 'Other' for w in batch), 2)
            self.assertEqual({w['domain'] for w in batch}, {'Emotions & Relationships'})


if __name__ == "__main__":
    unittest.main()
