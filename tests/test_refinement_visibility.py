from copy import deepcopy
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from domain.services.refinement_archive import report_applies_to_draft


LYRICS = "[Verse 1]\nCan you give me a hand?"
REPORT = {
    "raw_lyrics": LYRICS,
    "overall_score": 88,
    "line_breakdown": [{"line": "Can you give me a hand?", "score": 88, "comment": "Natural"}],
    "passed_count": 0, "warn_count": 1, "flagged_count": 0,
}
SCRIPT = '''
from presentation.tabs.tab3_refinement import render_tab_refinement
render_tab_refinement()
'''


class RefinementVisibilityTests(unittest.TestCase):
    def setup_state(self, mode=True, draft=LYRICS):
        self.state = {
            "draft_input": draft, "concept": "A diner", "domain": "Street & Daily Life",
            "critic_only_mode": mode, "critic_only_report": deepcopy(REPORT),
            "graph_report": {"input_lyrics": LYRICS, "final_lyrics": LYRICS + "\nThanks for your help.",
                             "overall_score": 88, "line_breakdown": deepcopy(REPORT["line_breakdown"])},
        }
        self.loader = patch("db.load_refinement_state", side_effect=lambda: deepcopy(self.state))
        self.saver = patch("db.save_refinement_state", side_effect=lambda **kwargs: self.state.update(deepcopy(kwargs)))
        self.loader.start()
        self.saver.start()
        self.addCleanup(self.loader.stop)
        self.addCleanup(self.saver.stop)
        app = AppTest.from_string(SCRIPT, default_timeout=15)
        app.session_state["target_batch"] = [{"word": "hand", "id": 1, "pos_type": "Noun"}]
        return app

    def test_blank_input_does_not_display_restored_critic(self):
        app = self.setup_state(draft="").run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.metric), 0)
        self.assertFalse(any("Copy manual refine" in item.label for item in app.get("popover")))

    def test_edit_and_clear_hide_results_and_survive_new_session(self):
        app = self.setup_state().run()
        self.assertFalse(app.exception)
        self.assertGreater(len(app.metric), 0)
        app.text_area(key="refine_draft").set_value("New lyrics").run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.metric), 0)
        self.assertTrue(any("الكلمات اتغيرت" in item.value for item in app.warning))
        app.text_area(key="refine_draft").set_value("").run()
        self.assertEqual(self.state["draft_input"], "")
        restored = AppTest.from_string(SCRIPT, default_timeout=15).run()
        self.assertFalse(restored.exception)
        self.assertEqual(len(restored.metric), 0)
        self.assertFalse(restored.text_area)
        self.assertIsNotNone(self.state["critic_only_report"])

    def test_pipeline_report_belongs_to_input_and_output_only(self):
        app = self.setup_state(mode=False).run()
        self.assertFalse(app.exception)
        self.assertGreater(len(app.metric), 0)
        app.text_area(key="refine_draft").set_value("").run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.metric), 0)
        self.assertFalse(any("Final Polished Lyrics" in item.label for item in app.expander))
        report = self.state["graph_report"]
        self.assertTrue(report_applies_to_draft(report, LYRICS))
        self.assertTrue(report_applies_to_draft(report, report["final_lyrics"]))
        self.assertFalse(report_applies_to_draft(report, "[Verse 1]"))

    def test_graph_explicitly_cleared_does_not_rehydrate_on_rerun(self):
        app = self.setup_state(mode=False).run()
        app.session_state["graph_report"] = None
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.metric), 0)


if __name__ == "__main__":
    unittest.main()
