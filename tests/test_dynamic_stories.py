import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from constants import DOMAINS, GENRES, SONG_STRUCTURES
from data.repositories.song_repository import get_recent_story_concepts
from data.services.gemini_service import analyze_vocabulary_mood, build_analysis_prompt, curate_thematic_vocabulary_batch
from domain.services.prompt_service import generate_master_prompt


class DynamicStoryTests(unittest.TestCase):
    def test_random_analysis_all_domains_uses_history_without_clock_or_prop_scaffold(self):
        for domain in DOMAINS + ['All Domains']:
            with self.subTest(domain=domain), patch(
                'data.services.gemini_service.get_recent_story_concepts', return_value=['A rejected apology.']
            ) as recent:
                prompt = build_analysis_prompt(['reply', 'firmly'], domain)
                recent.assert_called_once_with(domain)
                self.assertIn('A rejected apology.', prompt)
                self.assertIn('DYNAMIC STORY DESIGN', prompt)
                self.assertNotIn('Suggested Time of Day:', prompt)
                self.assertNotIn('Authentic Sensory Props', prompt)
                self.assertNotIn('Narrative Arc & Resolution Tone:', prompt)
                self.assertIn('Do not automatically end with reconciliation', prompt)

    def test_smart_pull_all_domains_uses_same_policy_and_source_constraints(self):
        response = json.dumps({'creative_concept': 'A friend declines an apology.',
                               'genre': GENRES[0], 'song_structure': SONG_STRUCTURES[0],
                               'selected_nouns': [], 'selected_verbs': ['reply'],
                               'selected_adjectives': ['firmly'], 'mood_breakdown': {'Dramatic / Intense': 100}})
        for domain in DOMAINS + ['All Domains']:
            with self.subTest(domain=domain), patch(
                'data.services.gemini_service.get_recent_story_concepts', return_value=['A celebration.']
            ), patch('data.services.fallback_engine.generate_with_fallback', return_value=(response, 0)) as generate:
                result = curate_thematic_vocabulary_batch([], ['reply'], ['firmly'], domain_focus=domain,
                    target_nouns=0, target_verbs=1, target_modifiers=1,
                    domain_quotas={'Verb': {domain: 1}}, candidate_domains={'reply': domain})
                self.assertTrue(result['success'])
                prompt = generate.call_args.kwargs['prompt']
                self.assertIn('A celebration.', prompt)
                self.assertIn('DYNAMIC STORY DESIGN', prompt)
                self.assertIn('Required source counts per POS', prompt)
                self.assertNotIn('Suggested Time of Day:', prompt)
                self.assertNotIn('Narrative Arc & Resolution Tone:', prompt)

    def test_existing_story_and_lyric_ending_are_preserved(self):
        concept = 'A daughter refuses to return home. Her father does not accept her choice.'
        with patch('data.services.gemini_service.get_recent_story_concepts', return_value=[concept]):
            prompt = build_analysis_prompt(['return'], 'Emotions & Relationships', existing_concept=concept)
        self.assertIn(concept, prompt)
        self.assertIn('preserve the exact characters, setting, and plot', prompt)
        self.assertIn('novelty check must NEVER rewrite it', prompt)
        for domain in DOMAINS:
            lyrics_prompt = generate_master_prompt(['return'], GENRES[0], SONG_STRUCTURES[0], {}, concept, domain)
            self.assertIn(concept, lyrics_prompt)
            self.assertIn('Do not add reconciliation, healing, a moral or optimism automatically', lyrics_prompt)

    def test_recent_history_filters_domain_and_does_not_mutate_data(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'stories.db'
            with closing(sqlite3.connect(path)) as conn, conn:
                conn.execute('CREATE TABLE songs (id INTEGER PRIMARY KEY, source_domain TEXT, creative_concept TEXT)')
                conn.executemany('INSERT INTO songs VALUES (?, ?, ?)', [
                    (1, 'Business & Career', 'An offer is declined.'),
                    (2, 'Emotions & Relationships', 'A goodbye.'),
                    (3, 'Business & Career', 'A shared success.'),
                    (4, None, 'An untagged story.'),
                    (5, 'Business & Career', '')])
            before = path.read_bytes()
            self.assertEqual(get_recent_story_concepts('Business & Career', 1, path), ['A shared success.'])
            self.assertEqual(len(get_recent_story_concepts('All Domains', db_path=path)), 4)
            self.assertEqual(get_recent_story_concepts('Basic / Neutral', db_path=path), [])
            self.assertEqual(path.read_bytes(), before)

    def test_legacy_history_failure_does_not_migrate_or_block_prompt(self):
        with patch('data.services.gemini_service.get_recent_story_concepts', side_effect=sqlite3.OperationalError):
            prompt = build_analysis_prompt(['reply'], 'Business & Career')
        self.assertIn('DYNAMIC STORY DESIGN', prompt)

    def test_api_failure_does_not_invent_a_happy_mood(self):
        with patch('data.services.gemini_service.get_recent_story_concepts', return_value=[]), patch(
            'data.services.fallback_engine.generate_with_fallback', side_effect=RuntimeError('offline')
        ):
            result = analyze_vocabulary_mood(['leave'], 'Emotions & Relationships', existing_concept='A goodbye without reconciliation.')
            self.assertFalse(result['success'])
            self.assertEqual(result['mood_breakdown'], {})
            self.assertEqual(result['creative_concept'], 'A goodbye without reconciliation.')
            curated = curate_thematic_vocabulary_batch([], ['leave'], ['firmly'], domain_focus='Business & Career')
            self.assertFalse(curated['success'])
            self.assertEqual(curated['mood_breakdown'], {})


if __name__ == '__main__':
    unittest.main()
