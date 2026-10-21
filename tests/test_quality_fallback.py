import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from data.services import fallback_engine as engine


class RateLimitError(Exception):
    code = 429


class QualityFallbackTests(unittest.TestCase):
    def setUp(self):
        self.keys = ['test-key-one', 'test-key-two', 'test-key-three']
        self.calls = []
        self.factory_patch = patch.object(engine, 'get_gemini_client', side_effect=self.client)
        self.keys_patch = patch.object(engine, 'get_gemini_api_keys', return_value=self.keys)
        self.factory_patch.start()
        self.keys_patch.start()
        self.addCleanup(self.factory_patch.stop)
        self.addCleanup(self.keys_patch.stop)
        self.addCleanup(setattr, engine, '_KEY_ROTATION_COUNTER', engine._KEY_ROTATION_COUNTER)
        self.addCleanup(setattr, engine, '_LAST_WORKING_INDEX', engine._LAST_WORKING_INDEX)
        self.fail = lambda model, key: False

    def client(self, api_key):
        def generate(model, contents, config):
            self.calls.append((model, api_key, config))
            if self.fail(model, api_key):
                raise RateLimitError('quota reached for ' + api_key)
            return SimpleNamespace(text='{"ok":true}')
        return SimpleNamespace(models=SimpleNamespace(generate_content=Mock(side_effect=generate)))

    def quality(self, **kwargs):
        return engine.generate_with_fallback('test', require_json=True,
            model_chain=engine.CRITIC_FALLBACK_CHAIN, **kwargs)

    def test_all_keys_on_38_before_37(self):
        self.fail = lambda model, key: model == 'gemini-3.8-flash'
        raw, index = self.quality()
        self.assertEqual(index, 1)
        self.assertEqual(raw, '{"ok":true}')
        self.assertEqual([(m, k) for m, k, _ in self.calls], [
            ('gemini-3.8-flash', key) for key in self.keys] + [('gemini-3.7-flash', self.keys[0])])
        for _, _, config in self.calls:
            self.assertEqual(config.http_options.retry_options.attempts, 1)
            self.assertEqual(config.response_mime_type, 'application/json')
            self.assertIsNone(config.thinking_config)

    def test_36_is_only_reached_after_every_key_on_38_and_37(self):
        self.fail = lambda model, key: model != 'gemini-3.6-flash'
        _, index = self.quality()
        self.assertEqual(index, 2)
        expected = [(model, key) for model in engine.CRITIC_FALLBACK_CHAIN[:2] for key in self.keys]
        self.assertEqual([(m, k) for m, k, _ in self.calls], expected + [('gemini-3.6-flash', self.keys[0])])

    def test_total_failure_stops_without_lower_models_and_redacts_keys(self):
        self.fail = lambda model, key: True
        with self.assertLogs(engine.logger, level='WARNING') as logs:
            with self.assertRaisesRegex(RuntimeError, 'No lower model was used'):
                self.quality()
        self.assertEqual([(m, k) for m, k, _ in self.calls],
            [(m, k) for m in ['gemini-3.8-flash', 'gemini-3.7-flash', 'gemini-3.6-flash'] for k in self.keys])
        for key in self.keys:
            self.assertNotIn(key, '\n'.join(logs.output))
        self.assertIn('code=429', '\n'.join(logs.output))
        self.assertIn('after ', '\n'.join(logs.output))

    def test_each_quality_request_restarts_at_38_key_one(self):
        engine._KEY_ROTATION_COUNTER = 2
        engine._LAST_WORKING_INDEX = 3
        self.quality(start_index=2)
        self.quality()
        self.assertEqual([(m, k) for m, k, _ in self.calls], [('gemini-3.8-flash', self.keys[0])] * 2)
        self.assertEqual(engine._KEY_ROTATION_COUNTER, 2)

    def test_routine_requests_keep_their_own_chain_and_key_rotation(self):
        engine._KEY_ROTATION_COUNTER = 1
        engine._LAST_WORKING_INDEX = 0
        engine.generate_with_fallback('routine')
        engine.generate_with_fallback('routine')
        self.assertEqual([(m, k) for m, k, _ in self.calls],
            [(engine.ROUTINE_STUDIO_CHAIN[0], self.keys[1]), (engine.ROUTINE_STUDIO_CHAIN[0], self.keys[2])])
        self.assertIsNone(self.calls[0][2].http_options)

    def test_no_keys_fail_before_contacting_api(self):
        with patch.object(engine, 'get_gemini_api_keys', return_value=[]):
            with self.assertRaisesRegex(ValueError, 'No Gemini API keys'):
                self.quality()
        self.assertEqual(self.calls, [])


if __name__ == '__main__':
    unittest.main()
