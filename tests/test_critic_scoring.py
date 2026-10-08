import json
import unittest
from unittest.mock import patch

from scripts.lyrics_graph import authenticity_critic_node, run_critic_only


class CriticScoringTests(unittest.TestCase):
    def evaluate(self, mode, drops, lines=None, theme="Science, Tech & Academia"):
        response = {
            "overall_score": 12,  # Ignore the model's coverage-biased aggregate.
            "dropped_words": drops,
            "lines_review": lines if lines is not None else [
                {"line": "He taught at the university.", "score": 95},
                {"line": "I read the letters.", "score": 85},
                {"line": "I read the letters.", "score": 85},
            ],
        }
        with patch("scripts.lyrics_graph.generate_with_fallback",
                   return_value=(json.dumps(response), 0)) as generate:
            if mode == "only":
                result = run_critic_only("[Verse]\nHe taught at the university.",
                                         ["university", "analysis", "input"], theme,
                                         "Lo-Fi / Chillhop", "Reading family letters")
            else:
                _, result = authenticity_critic_node({
                    "draft_lyrics": "[Verse]\nHe taught at the university.",
                    "target_words": ["university", "analysis", "input"],
                    "theme_category": theme, "genre": "Lo-Fi / Chillhop",
                    "core_concept": "Reading family letters", "active_model_index": 0,
                    "validation_errors": ["Missing target words: analysis, input"],
                    "permanently_dropped_words": ["storage"],
                })
            return result, generate.call_args.args[0]

    def test_drops_do_not_change_mean_in_either_mode(self):
        for mode in ("only", "loop"):
            for drops in ([], ["analysis", "input", "storage"]):
                with self.subTest(mode=mode, drops=drops):
                    result, prompt = self.evaluate(mode, drops)
                    self.assertEqual(result["overall_score"], 88)
                    self.assertIn("must NEVER lower line scores", prompt)
                    rows = result.get("line_breakdown", result.get("lines_review"))
                    self.assertEqual([r["status"] for r in rows], ["✅", "⚠️", "⚠️"])

    def test_empty_reviews_never_use_model_aggregate(self):
        for mode in ("only", "loop"):
            result, _ = self.evaluate(mode, [], lines=[])
            self.assertEqual(result["overall_score"], 0)

    def test_science_calibration_reaches_both_prompts(self):
        for mode in ("only", "loop"):
            _, prompt = self.evaluate(mode, [])
            self.assertIn("Accept moderately formal, educated spoken English", prompt)
            self.assertIn("Not everything needs analysis.", prompt)
            self.assertIn("Still flag a genuinely wrong meaning", prompt)
            self.assertIn("Normal chorus repetition is not an authenticity flaw", prompt)
            self.assertIn("A real song rarely has every line above 90. If almost all your scores are 90+, re-check yourself.", prompt)
            _, other_prompt = self.evaluate(mode, [], theme="Street & Daily Life")
            self.assertIn("A real song rarely has every line above 90. If almost all your scores are 90+, re-check yourself.", other_prompt)
            self.assertNotIn("Accept moderately formal, educated spoken English", other_prompt)


if __name__ == "__main__":
    unittest.main()
