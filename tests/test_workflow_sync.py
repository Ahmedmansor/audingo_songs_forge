from contextlib import ExitStack
from functools import partial
import gc
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import db
from data.database.connection import init_db, get_connection
from streamlit.testing.v1 import AppTest

SCRIPT = '''
from presentation.components.session import init_session_state
from presentation.tabs.tab2_studio import render_tab_studio
from presentation.tabs.tab3_refinement import render_tab_refinement
from presentation.tabs.tab4_commit_lab import render_tab_commit_lab
init_session_state()
render_tab_studio()
render_tab_refinement()
render_tab_commit_lab()
'''


class WorkflowSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(gc.collect)
        self.path = Path(self.temp.name) / "workflow.db"
        init_db(self.path)
        groups = {
            "Noun": "hand table friend door phone shop home team plan room chair",
            "Verb": "call help wait work need talk walk",
            "Adjective": "ready tired happy late calm",
        }
        with get_connection(self.path) as conn:
            for pos, words in groups.items():
                for word in words.split():
                    conn.execute("INSERT INTO ngsl_words (word,lemma_family,pos_type,domain_coca) VALUES (?,?,?,?)", (word, word, pos, "Basic / Neutral"))
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for name in dir(db):
            function = getattr(db, name)
            if callable(function) and hasattr(function, "__code__") and "db_path" in function.__code__.co_varnames[:function.__code__.co_argcount]:
                self.stack.enter_context(patch.object(db, name, partial(function, db_path=self.path)))
        self.stack.enter_context(patch("presentation.tabs.tab4_commit_lab.load_nlp", return_value=None))
        self.stack.enter_context(patch("pipeline.process_song_text", side_effect=lambda **kw: {
            "green": ["hand"] if "hand" in kw["target_words"] else [],
            "red": [w for w in kw["target_words"] if w != "hand"], "blue": [], "reused": [], "yellow": [],
        }))
        self.critic = self.stack.enter_context(patch("presentation.tabs.tab3_refinement.run_critic_only", side_effect=lambda **kw: {
            "raw_lyrics": kw["draft"], "overall_score": 95,
            "line_breakdown": [{"line": kw["draft"].splitlines()[-1], "score": 95, "comment": "Natural"}],
            "context": {"target_words": kw["target_words"], "genre": kw["genre"]},
        }))

    @staticmethod
    def button(app, label):
        return next(item for item in app.button if label in item.label)

    def selected_app(self):
        app = AppTest.from_string(SCRIPT, default_timeout=20).run()
        self.assertFalse(app.exception)
        self.button(app, "Random 20").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state["target_batch"]), 20)
        return app

    def test_selection_music_critic_swap_clear_and_refresh(self):
        app = self.selected_app()
        genre = next(item for item in app.selectbox if item.label == "Genre (Closed List)")
        genre.select("Jazz / Bossa Nova").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.text_input(key="refine_genre").value, "Jazz / Bossa Nova")
        self.assertEqual(app.text_input(key="refine_theme").value, "All Domains")
        app.text_area(key="refine_draft").set_value("[Verse 1]\nCan you give me a hand?").run()
        self.button(app, "Run critic").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(self.critic.call_args.kwargs["genre"], "Jazz / Bossa Nova")
        self.assertEqual(len(self.critic.call_args.kwargs["target_words"]), 20)
        self.button(app, "Send reviewed lyrics").click().run()
        self.assertFalse(app.exception)
        self.assertIn("hand?", app.text_area(key="commit_lyrics").value)
        self.button(app, "Analyze Song").click().run()
        self.assertIsNotNone(app.session_state["analysis_results"])
        before = [word["word"] for word in app.session_state["target_batch"]]
        self.button(app, "Swap").click().run()
        self.assertFalse(app.exception)
        self.assertNotEqual(before, [word["word"] for word in app.session_state["target_batch"]])
        self.assertIsNone(app.session_state["critic_only_report"])
        self.assertIsNone(app.session_state["analysis_results"])
        self.assertIn("hand?", app.text_area(key="refine_draft").value)
        self.button(app, "Clear").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["target_batch"], [])
        self.assertFalse(any(item.key in ("refine_draft", "commit_lyrics") for item in app.text_area))
        restored = AppTest.from_string(SCRIPT, default_timeout=20).run()
        self.assertFalse(restored.exception)
        self.assertEqual(restored.session_state["target_batch"], [])
        self.assertFalse(db.load_refinement_state().get("critic_only_report"))

    def test_edited_commit_lyrics_requires_new_analysis(self):
        app = self.selected_app()
        app.text_area(key="commit_lyrics").set_value("Can you give me a hand?").run()
        self.button(app, "Analyze Song").click().run()
        self.assertIsNotNone(app.session_state["analysis_results"])
        app.text_area(key="commit_lyrics").set_value("Different lyrics.").run()
        self.assertFalse(app.exception)
        self.assertIsNone(app.session_state["analysis_results"])
        self.assertFalse(any("Approve & Save" in item.label for item in app.button))

    def test_reviewed_title_transfers_and_remains_editable(self):
        app = self.selected_app()
        app.text_input(key="commit_song_title_input_field").set_value("Old title").run()
        app.text_area(key="refine_draft").set_value(
            "[Title]: Grandpa's Letters\n[Verse 1]\nCan you give me a hand?"
        ).run()
        self.button(app, "Run critic").click().run()
        self.button(app, "Send reviewed lyrics").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.text_input(key="commit_song_title_input_field").value, "Grandpa's Letters")
        self.assertEqual(app.session_state["song_title_input"], "Grandpa's Letters")
        self.assertNotIn("[Title]", app.text_area(key="commit_lyrics").value)
        app.text_input(key="commit_song_title_input_field").set_value("Edited title").run()
        self.assertEqual(app.session_state["song_title_input"], "Edited title")
        app.text_area(key="refine_draft").set_value("[Title]:\n[Verse 1]\nCan you give me a hand?").run()
        self.button(app, "Send reviewed lyrics").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.text_input(key="commit_song_title_input_field").value, "Edited title")

    def test_reset_token_discards_old_browser_state(self):
        app = self.selected_app()
        with get_connection(self.path) as conn:
            conn.execute("DELETE FROM app_state WHERE key IN ('active_session','refinement_state')")
            conn.execute("INSERT INTO app_state(key,value) VALUES ('workspace_reset_token','fresh')")
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["target_batch"], [])
        self.assertFalse(any(item.key == "refine_draft" for item in app.text_area))

    def test_approval_archives_current_critic_and_ends_active_work(self):
        import json
        app = self.selected_app()
        batch = [word["word"] for word in app.session_state["target_batch"]]
        app.text_area(key="refine_draft").set_value("[Verse 1]\nCan you give me a hand?").run()
        self.button(app, "Run critic").click().run()
        self.button(app, "Send reviewed lyrics").click().run()
        app.text_input(key="commit_song_title_input_field").set_value("New song").run()
        app.session_state["studio_poster_prompt"] = "Poster already prepared"
        app.session_state["studio_suno_prompt"] = "Music already prepared"
        self.button(app, "Analyze Song").click().run()
        self.button(app, "Approve & Save").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["target_batch"], [])
        self.assertFalse(any(item.key in ("refine_draft", "commit_lyrics") for item in app.text_area))
        saved = db.get_all_songs().iloc[0]
        self.assertEqual(saved.source_domain, app.session_state["selected_domain"])
        snapshot = json.loads(saved.refinement_report)
        self.assertEqual(snapshot["report"]["context"]["target_words"], batch)
        self.assertEqual(snapshot["report"]["overall_score"], 95)
        self.assertEqual(len(db.get_track_variants(int(saved.id))), 1)
        self.assertFalse(db.load_active_batch_state())
        self.assertIsNone(db.load_refinement_state().get("critic_only_report"))


if __name__ == "__main__":
    unittest.main()
