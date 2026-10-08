"""
app.py — Audingo Songs Forge Streamlit Application.
Main entry point orchestrating clean presentation tabs and modular architecture.
"""

import streamlit as st
from dotenv import load_dotenv

# Load environment variables (e.g. GEMINI_API_KEY)
load_dotenv()

# Database & Schema Initialization
import db
db.init_db()

# Page configuration
st.set_page_config(
    page_title="Audingo Songs Forge | NGSL Studio",
    page_icon=":material/graphic_eq:",
    layout="wide",
    initial_sidebar_state="auto"
)

# Presentation Layer Imports
from presentation.styles import apply_custom_styles
from presentation.components.appearance import render_appearance_switch
from presentation.components.identity import icon_svg
from presentation.components.session import init_session_state
from presentation.components.sidebar import render_sidebar
from presentation.tabs.tab1_dictionary import render_tab_dictionary
from presentation.tabs.tab2_studio import render_tab_studio
from presentation.tabs.tab3_refinement import render_tab_refinement
from presentation.tabs.tab4_commit_lab import render_tab_commit_lab
from presentation.tabs.tab5_library import render_tab_library

# 1. Apply UI theme & styles
render_appearance_switch()
apply_custom_styles()

# 2. Initialize Session State & Persisted DB Sync
init_session_state()

# 3. Render Modern Mastery Sidebar
render_sidebar()

# 4. Workspace identity
st.html(f"""<header class="studio-hero">
<div><div class="studio-eyebrow">Audingo / Songs Forge</div>
<h1>Words become music.</h1>
<p>A thoughtful space to discover vocabulary, craft lyrics,<br>and create songs that stay with you.</p></div>
<div class="hero-art" aria-hidden="true">{icon_svg()}</div>
</header>""")

# 5. Primary feature tabs: keep widget state across the complete workflow.
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    ":material/menu_book: Dictionary",
    ":material/tune: Studio",
    ":material/auto_awesome: Refinement",
    ":material/fact_check: Commit Lab",
    ":material/library_music: Library",
])

with tab1:
    render_tab_dictionary()

with tab2:
    render_tab_studio()

with tab3:
    render_tab_refinement()

with tab4:
    render_tab_commit_lab()

with tab5:
    render_tab_library()
