"""
session.py — Session state initialization and persistent sync with SQLite.
"""

import streamlit as st
from constants import GENRES, SONG_STRUCTURES
import db


def init_session_state():
    """Initializes Streamlit session state from persisted SQLite session."""
    persisted_session = db.load_active_batch_state()

    if "target_batch" not in st.session_state:
        st.session_state.target_batch = persisted_session.get("target_batch", [])

    if "mood_analysis" not in st.session_state:
        st.session_state.mood_analysis = persisted_session.get("mood_analysis", None)

    if "master_prompt" not in st.session_state:
        st.session_state.master_prompt = persisted_session.get("master_prompt", "")

    if "studio_suno_prompt" not in st.session_state:
        st.session_state.studio_suno_prompt = persisted_session.get("suno_prompt", "")

    if "studio_poster_prompt" not in st.session_state:
        st.session_state.studio_poster_prompt = persisted_session.get("poster_prompt", "")

    if "selected_genre" not in st.session_state:
        st.session_state.selected_genre = persisted_session.get("selected_genre", GENRES[0])

    if "selected_vocalist" not in st.session_state:
        st.session_state.selected_vocalist = persisted_session.get("selected_vocalist", "Male")

    if "selected_structure" not in st.session_state:
        st.session_state.selected_structure = persisted_session.get("selected_structure", SONG_STRUCTURES[0])

    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None

    if "raw_lyrics_input" not in st.session_state:
        st.session_state.raw_lyrics_input = ""

    if "song_title_input" not in st.session_state:
        st.session_state.song_title_input = ""

    if "title_has_error" not in st.session_state:
        st.session_state.title_has_error = False

    if "custom_concept" not in st.session_state:
        st.session_state.custom_concept = persisted_session.get("custom_concept", "")

    if "commit_success_message" not in st.session_state:
        st.session_state.commit_success_message = None

    if "selected_domain" not in st.session_state:
        st.session_state.selected_domain = persisted_session.get("selected_domain", "All Domains")


def sync_active_session():
    """Sync current studio batch and musical direction to SQLite for F5 persistence."""
    if st.session_state.target_batch:
        db.save_active_batch_state(
            batch=st.session_state.target_batch,
            concept=st.session_state.get("custom_concept", ""),
            genre=st.session_state.get("selected_genre", GENRES[0]),
            song_structure=st.session_state.get("selected_structure", SONG_STRUCTURES[0]),
            mood_analysis=st.session_state.get("mood_analysis", None),
            master_prompt=st.session_state.get("master_prompt", ""),
            suno_prompt=st.session_state.get("studio_suno_prompt", ""),
            poster_prompt=st.session_state.get("studio_poster_prompt", ""),
            vocalist=st.session_state.get("selected_vocalist", "Male"),
            selected_domain=st.session_state.get("selected_domain", "All Domains")
        )
    else:
        db.clear_active_batch_state()
