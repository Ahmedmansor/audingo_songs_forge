"""Shared visual styling for the Audingo workspace."""
from pathlib import Path
import streamlit as st


def apply_custom_styles():
    """Share the native theme with custom cards, including older inline HTML."""
    from presentation.theme import palette
    tokens = palette(st.session_state.get("ui_theme_mode", "dark"))
    css = Path(__file__).with_name("theme.css").read_text(encoding="utf-8")
    variables = ";".join(f"--studio-{key}:{value}" for key, value in tokens.items())
    st.html(f"<style>{css}\n:root {{{variables}}}</style>")
