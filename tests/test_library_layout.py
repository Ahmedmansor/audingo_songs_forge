from contextlib import ExitStack
from functools import partial
import gc
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import db
from data.database.connection import init_db
from presentation.components.identity import sidebar_domain_progress
from streamlit.testing.v1 import AppTest

SCRIPT = "from presentation.tabs.tab5_library import render_tab_library\nrender_tab_library()"


class LibraryLayoutTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.addCleanup(gc.collect)
        self.path = Path(temp.name) / "library.db"
        init_db(self.path)
        stack = ExitStack()
        self.addCleanup(stack.close)
        for name in dir(db):
            function = getattr(db, name)
            if callable(function) and hasattr(function, "__code__") and "db_path" in function.__code__.co_varnames[:function.__code__.co_argcount]:
                stack.enter_context(patch.object(db, name, partial(function, db_path=self.path)))
        self.song_id = db.approve_and_save_song("A [quiet] evening", "Can you give me a hand?\n" * 80, ["hand"], [], [], genre="Pop", creative_concept="Friends cook dinner.")[0]
        self.other_id = db.approve_and_save_song("Another morning", "I'll call you when I'm done.", [], [], [])[0]
        self.variant_id = db.upsert_track_variant(self.song_id, "Pop", "Male", "Warm pop vocals", "A quiet kitchen")

    def open_song(self):
        app = AppTest.from_string(SCRIPT, default_timeout=20).run()
        app.selectbox(key="library_selected_song").select(self.song_id).run()
        self.assertFalse(app.exception)
        return app

    def test_compact_overview_and_literal_search(self):
        app = self.open_song()
        self.assertFalse(app.text_area)
        self.assertFalse(app.dataframe)
        self.assertTrue(all(not expander.proto.expanded for expander in app.expander))
        self.assertEqual(len(app.get("html")), 2)  # One song card and its collapsed lyrics.
        app.text_input(key="library_search").set_value("[quiet]").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox(key="library_selected_song").value, self.song_id)
        app.text_input(key="library_search").set_value("No match").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("No songs match" in info.value for info in app.info))

    def test_vocabulary_disclosure_and_package_edits(self):
        app = self.open_song()
        app.button_group(key=f"library_section_{self.song_id}").set_value("Vocabulary").run()
        self.assertFalse(app.exception)
        self.assertTrue(all(not expander.proto.expanded for expander in app.expander))
        app.button_group(key=f"library_section_{self.song_id}").set_value("Production").run()
        self.assertFalse(app.exception)
        app.text_area(key=f"txt_suno_{self.variant_id}").set_value("Updated pop style")
        next(button for button in app.button if button.label == "Save package").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(db.get_track_variants(self.song_id)[0]["suno_prompt"], "Updated pop style")
        app.button_group(key=f"package_prompt_{self.variant_id}").set_value("Cover").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.code[0].value, "A quiet kitchen")

    def test_overview_totals_authenticity_and_visible_domain_chart(self):
        songs = db.get_all_songs()
        index = songs.index[songs.id == self.song_id][0]
        songs.loc[index, "bonus_words"] = "kitchen, dinner"
        songs.loc[index, "reused_words"] = "friend"
        snapshot = {"evaluated_lyrics": songs.loc[index, "lyrics"], "report": {"overall_score": 94}}
        songs.loc[index, "refinement_report"] = json.dumps(snapshot)
        with patch.object(db, "get_all_songs", return_value=songs), patch(
            "presentation.tabs.tab5_library.render_domain_breakdown_section"
        ) as chart, patch.object(db, "compute_domain_breakdown", return_value={"total_words": 4}) as breakdown:
            app = self.open_song()
            card = app.get("html")[0].proto.body
            self.assertIn("<b>3</b><span>Total new words", card)
            self.assertIn("<b>94%</b><span>Authenticity score", card)
            chart.assert_called_with({"total_words": 4}, title="Domain breakdown", compact=True)
            breakdown.assert_called_with(["dinner", "friend", "hand", "kitchen"])
            songs.loc[index, "lyrics"] = "Changed lyrics."
            app.run()
            self.assertIn("Authenticity · archived", app.get("html")[0].proto.body)
            songs.loc[index, "refinement_report"] = None
            app.run()
            self.assertIn("<b>—</b><span>Authenticity · not recorded", app.get("html")[0].proto.body)

    def test_song_editor_still_saves_and_switches_songs(self):
        app = self.open_song()
        app.button_group(key=f"library_section_{self.song_id}").set_value("Edit").run()
        self.assertFalse(app.exception)
        app.text_input(key=f"edit_title_{self.song_id}").set_value("A better evening")
        next(button for button in app.button if "Save updates" in button.label).click().run()
        self.assertFalse(app.exception)
        row = db.get_all_songs().query("id == @self.song_id").iloc[0]
        self.assertEqual(row.title, "A better evening")
        app.selectbox(key="library_selected_song").select(self.other_id).run()
        self.assertFalse(app.exception)
        self.assertFalse(app.text_area)  # A new song opens on Overview.

    def test_sidebar_coverage_uses_consumed_words_and_handles_empty_domain(self):
        html = sidebar_domain_progress("Business & Career", {"total": 40, "used": 10, "unused": 30})
        self.assertIn('aria-valuenow="25.0"', html)
        self.assertIn("10 / 40 covered", html)
        self.assertIn("30 left", html)
        self.assertIn('aria-valuenow="0.0"', sidebar_domain_progress("Empty", {"total": 0, "used": 0}))


if __name__ == "__main__":
    unittest.main()
