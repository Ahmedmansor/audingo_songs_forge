"""
session.py — Session state initialization and persistent sync with SQLite.
"""

import streamlit as st
from constants import GENRES, SONG_STRUCTURES
import db


def invalidate_workflow(clear_lyrics=True):
    """Invalidate derived work without touching songs already saved in Library."""
    for key in ("graph_report", "critic_only_report", "graph_time", "critic_only_time", "analysis_results", "word_fit_audit"):
        st.session_state[key] = None
    st.session_state["_refinement_reports_loaded"] = True
    st.session_state.pop("_commit_analysis_signature", None)
    if clear_lyrics:
        st.session_state["raw_lyrics_input"] = ""
        st.session_state["song_title_input"] = ""
        st.session_state["_reset_workflow_widgets"] = True
    db.save_refinement_state(
        draft_input="" if clear_lyrics else st.session_state.get("refine_draft", ""),
        concept=st.session_state.get("custom_concept", ""),
        domain=st.session_state.get("selected_domain", "All Domains"),
    )


def set_target_batch(batch, keep_direction=False, clear_lyrics=True):
    """The word selection is the root of the active songwriting session."""
    st.session_state["target_batch"] = batch
    st.session_state["mood_analysis"] = None
    for key in ("master_prompt", "studio_suno_prompt", "studio_poster_prompt"):
        st.session_state[key] = ""
    if not keep_direction:
        st.session_state["custom_concept"] = ""
    invalidate_workflow(clear_lyrics=clear_lyrics)


def apply_pending_workflow_reset():
    if st.session_state.pop("_reset_workflow_widgets", False):
        for key in ("refine_draft", "refine_concept", "commit_lyrics", "commit_song_title_input_field"):
            st.session_state[key] = ""
        st.session_state.pop("pending_draft_update", None)


def direction_signature():
    return tuple(st.session_state.get(key, "") for key in (
        "selected_domain", "selected_genre", "selected_structure", "selected_vocalist", "custom_concept"
    ))


def init_session_state():
    """Initializes Streamlit session state from persisted SQLite session."""
    reset_token = db.get_workspace_reset_token()
    if reset_token and st.session_state.get("_workspace_reset_token") != reset_token:
        for key in (
            "target_batch", "mood_analysis", "master_prompt", "studio_suno_prompt", "studio_poster_prompt",
            "custom_concept", "selected_domain", "selected_genre", "selected_structure", "selected_vocalist",
            "graph_report", "critic_only_report", "graph_time", "critic_only_time", "word_fit_audit",
            "analysis_results", "raw_lyrics_input", "song_title_input", "refine_draft", "refine_concept",
            "refine_domain", "refine_theme", "refine_genre", "commit_lyrics", "commit_song_title_input_field",
            "_refinement_reports_loaded", "_commit_analysis_signature", "pending_draft_update",
            "_direction_signature", "commit_success_message", "studio_domain_selector",
        ):
            st.session_state.pop(key, None)
    st.session_state["_workspace_reset_token"] = reset_token
    apply_pending_workflow_reset()
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

    if "blend_joker" not in st.session_state:
        st.session_state.blend_joker = True

    if "graph_report" not in st.session_state:
        st.session_state.graph_report = None

    if "word_fit_audit" not in st.session_state:
        st.session_state.word_fit_audit = persisted_session.get("word_fit_audit", None)

    st.session_state.setdefault("_direction_signature", direction_signature())


def sync_active_session(invalidate_direction=True):
    """Sync current studio batch and musical direction to SQLite for F5 persistence."""
    signature = direction_signature()
    if invalidate_direction and signature != st.session_state.get("_direction_signature", signature):
        invalidate_workflow(clear_lyrics=False)
        for key in ("master_prompt", "studio_suno_prompt", "studio_poster_prompt"):
            st.session_state[key] = ""
    st.session_state["_direction_signature"] = signature
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
            selected_domain=st.session_state.get("selected_domain", "All Domains"),
            word_fit_audit=st.session_state.get("word_fit_audit", None)
        )
    else:
        db.clear_active_batch_state()

