import unittest
from data.services.gemini_service import (
    build_analysis_prompt,
    build_vocab_story_audit_prompt,
)
from presentation.tabs.tab2_studio import is_active_song_in_progress
import streamlit as st


class StudioSafeguardsAndPromptsTests(unittest.TestCase):
    def test_analysis_story_prompt_is_specific_and_structured(self):
        words = ["door", "listen", "quiet", "key", "wait", "friend"]
        prompt = build_analysis_prompt(words)
        # Verify prompt requires high-fidelity, specific story elements
        self.assertIn("CRITICAL STORY CONCEPT INSTRUCTIONS (SPECIFIC, HIGH-FIDELITY STORYLINE ROADMAP)", prompt)
        self.assertIn("Specific Characters & Relationship", prompt)
        self.assertIn("Tangible Physical Setting & Sensory Atmosphere", prompt)
        self.assertIn("Core Human Stakes & Dramatic Tension", prompt)
        self.assertIn("Clear Narrative Progression", prompt)
        self.assertIn("Real Spoken Dialogue Anchors", prompt)
        self.assertIn("NO vague one-liners", prompt)

    def test_audit_prompt_is_fair_and_contextually_plausible(self):
        words = ["coffee", "table", "listen", "tired"]
        story = "Maya and Leo talking late at night in a diner about a difficult work decision."
        audit_prompt = build_vocab_story_audit_prompt(words, story)
        # Verify fairness and contextual plausibility standards
        self.assertIn("CRITICAL AUDITING PHILOSOPHY: FAIRNESS, REALISTIC DIALOGUE & CONTEXTUAL PLAUSIBILITY", audit_prompt)
        self.assertIn("PRINCIPLE OF FAIRNESS & PLURALITY", audit_prompt)
        self.assertIn("UNIVERSAL EXEMPTION FOR BASIC / NEUTRAL WORDS", audit_prompt)
        self.assertIn("PLAUSIBILITY TEST", audit_prompt)
        self.assertIn("BENEFIT OF THE DOUBT", audit_prompt)
        self.assertIn("STRICT HIGH THRESHOLD FOR FLAGGING", audit_prompt)

    def test_is_active_song_in_progress_safeguard(self):
        # Empty session state
        st.session_state.clear()
        self.assertFalse(is_active_song_in_progress())

        # With active target batch
        st.session_state["target_batch"] = [{"id": 1, "word": "friend", "pos_type": "Noun"}]
        self.assertTrue(is_active_song_in_progress())

        # Empty batch but with lyrics
        st.session_state["target_batch"] = []
        st.session_state["refine_draft"] = "[Verse 1]\nI'll call you when I'm done."
        self.assertTrue(is_active_song_in_progress())

        # Empty lyrics but with custom story concept
        st.session_state["refine_draft"] = ""
        st.session_state["custom_concept"] = "Two old friends reconciling over coffee."
        self.assertTrue(is_active_song_in_progress())

        # Empty concept but with master prompt
        st.session_state["custom_concept"] = ""
        st.session_state["master_prompt"] = "You are a songwriter..."
        self.assertTrue(is_active_song_in_progress())

        # Completely clean
        st.session_state["master_prompt"] = ""
        self.assertFalse(is_active_song_in_progress())


if __name__ == "__main__":
    unittest.main()
