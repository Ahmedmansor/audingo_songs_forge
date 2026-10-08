import json
import gc
import sqlite3
import tempfile
import unittest
from contextlib import ExitStack
from functools import partial
from pathlib import Path
from unittest.mock import patch

from data.database.connection import init_db, get_connection
from data.repositories.song_repository import approve_and_save_song, get_all_songs, update_song, delete_song
from domain.services.refinement_archive import select_refinement_snapshot, report_matches_lyrics, parse_refinement_snapshot


LYRICS = "[Verse 1]\nCan you give me a hand?\nI'll call you when I'm done."
REPORT = {
    "raw_lyrics": LYRICS,
    "overall_score": 93,
    "critic_name": "Daily critic",
    "domain": "Street & Daily Life",
    "model_used": "test-model",
    "line_breakdown": [
        {"line": "Can you give me a hand?", "score": 96, "comment": "Natural request"},
        {"line": "I'll call you when I'm done.", "score": 89, "issue": "Check delivery"},
    ],
    "dropped_words": ["orbit"],
}


class RefinementArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Existing repositories use sqlite transaction contexts; collect their
        # released connections before Windows removes temporary database files.
        self.addCleanup(gc.collect)
        self.path = Path(self.temp.name) / "test.db"
        init_db(self.path)

    def snapshot(self):
        return select_refinement_snapshot(LYRICS, {"critic_only_report": REPORT}, {})[0]

    def save(self, snapshot=None, title="Test song"):
        return approve_and_save_song(title, LYRICS, [], [], [], db_path=self.path, refinement_report=snapshot)[0]

    def test_layout_is_ignored_but_changes_and_repeated_choruses_are_not(self):
        snapshot = self.snapshot()
        self.assertTrue(report_matches_lyrics(snapshot, "[Lyrics]:\n\n" + LYRICS.replace("I'll", "I’ll")))
        self.assertFalse(report_matches_lyrics(snapshot, LYRICS.replace("hand?", "ride?")))
        self.assertFalse(report_matches_lyrics(snapshot, LYRICS + "\nCan you give me a hand?"))

    def test_modes_restore_matching_reports_and_explicit_clear(self):
        pipeline = {**REPORT, "final_lyrics": LYRICS, "iterations_used": 2}
        snapshot, stale = select_refinement_snapshot(LYRICS, {"critic_only_mode": False}, {"graph_report": pipeline})
        self.assertEqual(snapshot["mode"], "pipeline")
        self.assertFalse(stale)
        snapshot["report"]["line_breakdown"][0]["score"] = 0
        self.assertEqual(REPORT["line_breakdown"][0]["score"], 96)
        self.assertEqual(select_refinement_snapshot(LYRICS, {"critic_only_report": None}, {"critic_only_report": REPORT}), (None, False))
        self.assertEqual(select_refinement_snapshot("Different lyrics", {"critic_only_report": REPORT}, {}), (None, True))
        matching, _ = select_refinement_snapshot(LYRICS, {"critic_only_report": {**REPORT, "raw_lyrics": "Old"}, "graph_report": pipeline}, {})
        self.assertEqual(matching["mode"], "pipeline")

    def test_snapshot_roundtrip_independence_edits_and_deletion(self):
        song_id = self.save(self.snapshot())
        self.save(title="No critic")
        rows = get_all_songs(self.path)
        saved_raw = rows.loc[rows.id == song_id, "refinement_report"].iloc[0]
        saved = parse_refinement_snapshot(saved_raw)
        self.assertEqual(saved["report"], REPORT)
        self.assertIsNone(parse_refinement_snapshot(rows.iloc[0].refinement_report))
        update_song(song_id, "Renamed", "Edited lyrics", "", db_path=self.path)
        row = get_all_songs(self.path).query("id == @song_id").iloc[0]
        self.assertEqual(row.refinement_report, saved_raw)
        self.assertFalse(report_matches_lyrics(saved, row.lyrics))
        self.assertTrue(delete_song(song_id, db_path=self.path))
        self.assertEqual(len(get_all_songs(self.path)), 1)

    def test_upgrade_preserves_old_songs_and_is_idempotent(self):
        legacy = Path(self.temp.name) / "legacy.db"
        with sqlite3.connect(legacy) as conn:
            conn.execute("CREATE TABLE songs (id INTEGER PRIMARY KEY, title TEXT, lyrics TEXT, target_words TEXT, created_at TEXT)")
            conn.execute("INSERT INTO songs VALUES (1, 'Old', 'Words', '', '2026-01-01')")
        init_db(legacy)
        init_db(legacy)
        row = get_all_songs(legacy).iloc[0]
        self.assertEqual(row.title, "Old")
        self.assertIsNone(row.refinement_report)

    def test_report_does_not_change_word_count_semantics(self):
        with get_connection(self.path) as conn:
            conn.execute("INSERT INTO ngsl_words (word, lemma_family, pos_type) VALUES ('hand', 'hand', 'Noun')")
        song_id, ngsl_count, _ = approve_and_save_song(
            "Count", LYRICS, ["hand"], ["hand"], [], reused_words=["hand"],
            db_path=self.path, refinement_report=self.snapshot(),
        )
        self.assertEqual(ngsl_count, 1)
        with get_connection(self.path) as conn:
            self.assertEqual(conn.execute("SELECT usage_count FROM ngsl_words").fetchone()[0], 1)
        delete_song(song_id, db_path=self.path)
        with get_connection(self.path) as conn:
            self.assertEqual(conn.execute("SELECT usage_count FROM ngsl_words").fetchone()[0], 0)

    def test_invalid_saved_json_is_safe(self):
        for raw in (None, "broken", "[]", "null", {"report": []}):
            self.assertIsNone(parse_refinement_snapshot(raw))

    def test_commit_saves_report_and_library_reads_it_without_session(self):
        import db
        from streamlit.testing.v1 import AppTest
        import presentation.tabs.tab4_commit_lab as commit

        # Bind every facade DB function to the disposable database; never touch the live DB.
        with ExitStack() as stack:
            for name in dir(db):
                function = getattr(db, name)
                if callable(function) and hasattr(function, "__code__") and "db_path" in function.__code__.co_varnames[:function.__code__.co_argcount]:
                    stack.enter_context(patch.object(db, name, partial(function, db_path=self.path)))
            stack.enter_context(patch.object(commit, "load_nlp", return_value=None))
            app = AppTest.from_string('''
import streamlit as st
from presentation.components.session import init_session_state
from presentation.tabs.tab4_commit_lab import render_tab_commit_lab
init_session_state()
render_tab_commit_lab()
''', default_timeout=20)
            app.session_state["raw_lyrics_input"] = LYRICS
            app.session_state["target_batch"] = [{"word": "hand", "id": 1, "pos_type": "Noun"}]
            from domain.services.refinement_archive import lyrics_signature
            app.session_state["_commit_analysis_signature"] = (lyrics_signature(LYRICS), ("hand",))
            app.session_state["song_title_input"] = "Archived critic"
            app.session_state["analysis_results"] = {"green": [], "red": [], "blue": [], "reused": [], "yellow": []}
            app.session_state["critic_only_report"] = REPORT
            app.session_state["studio_poster_prompt"] = "Existing poster prompt"
            app.session_state["studio_suno_prompt"] = "Existing music prompt"
            app.run()
            self.assertFalse(app.exception)
            next(button for button in app.button if "Approve & Save" in button.label).click().run()
            self.assertFalse(app.exception)
            saved = get_all_songs(self.path).iloc[0]
            self.assertEqual(parse_refinement_snapshot(saved.refinement_report)["report"], REPORT)

            library = AppTest.from_string('''
from presentation.tabs.tab5_library import render_tab_library
render_tab_library()
''', default_timeout=20).run()
            self.assertFalse(library.exception)
            self.assertTrue(any("Natural request" in frame.value.to_string() for frame in library.dataframe))
            update_song(int(saved.id), "Archived critic", "Changed afterwards", "", db_path=self.path)
            library.run()
            self.assertFalse(library.exception)
            self.assertTrue(any("الكلمات الحالية" in warning.value for warning in library.warning))


if __name__ == "__main__":
    unittest.main()
