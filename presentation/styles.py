"""Shared visual styling for the Audingo workspace."""
from pathlib import Path
import streamlit as st


def apply_custom_styles():
    """Native widget colors live in config.toml; custom cards share theme.css."""
    st.html(Path(__file__).with_name("theme.css"))
