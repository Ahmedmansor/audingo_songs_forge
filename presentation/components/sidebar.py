"""Workspace identity, mastery summary, and service configuration."""
import os
from html import escape
import streamlit as st
import db
from constants import DOMAINS
from presentation.components.identity import icon_svg


def render_sidebar():
    with st.sidebar:
        stats = db.get_progress_stats()
        songs = db.get_all_songs()
        pct = max(0, min(float(stats.get("percent", 0)), 100))
        st.html(f'<div class="studio-brand"><div class="studio-mark">{icon_svg(color="#FFFFFF")}</div><div><strong>Audingo</strong><small>Songs Forge</small></div></div>')
        st.caption("YOUR WORKSPACE")
        st.subheader("A little closer, every song.")
        st.caption("Build your vocabulary, one song at a time.")
        with st.container(border=True):
            st.markdown(f"**NGSL mastery** · {pct:.1f}%")
            st.progress(pct / 100)
            st.caption(f"{stats['used']:,} of {stats['total']:,} words covered")
        left, right = st.columns(2)
        left.metric("Remaining", f"{stats['unused']:,}")
        right.metric("Songs", len(songs) if songs is not None else 0)
        st.caption(f"{stats['extra_count']:,} extra words discovered beyond NGSL")
        st.divider()
        st.markdown("**Explore your vocabulary**")
        st.caption("Words remaining by domain")
        domains = db.get_domain_detailed_stats()
        rows = ''.join(
            f'<div class="sidebar-domain">{icon_svg(name)}<span>{escape(name)}</span><b>{domains.get(name, {}).get("unused", 0):,}</b></div>'
            for name in DOMAINS
        )
        st.html(rows)
        st.space("small")
        if os.environ.get("GEMINI_API_KEY"):
            st.caption(":material/check_circle: Gemini · API key configured")
        else:
            st.caption(":material/key: Add a Gemini API key in .env to enable AI tools.")
