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
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Presentation Layer Imports
from presentation.styles import apply_custom_styles
from presentation.components.session import init_session_state
from presentation.components.sidebar import render_sidebar
from presentation.tabs.tab1_dictionary import render_tab_dictionary
from presentation.tabs.tab2_studio import render_tab_studio
from presentation.tabs.tab3_commit_lab import render_tab_commit_lab
from presentation.tabs.tab4_library import render_tab_library

# 1. Apply UI theme & styles
apply_custom_styles()

# 2. Initialize Session State & Persisted DB Sync
init_session_state()

# 3. Render Modern Mastery Sidebar
render_sidebar()

# 4. Main Page Header
st.markdown('<div class="main-header">Audingo Songs Forge</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">NGSL Vocabulary Targeting, AI Prompt Crafting, and Lyric Review Pipeline</div>', unsafe_allow_html=True)

# 5. Primary Feature Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dictionary & Analytics",
    "🎧 Studio (Word Selection & Prompt)",
    "🧪 Commit Lab (Review & Approval)",
    "🎵 Songs Library"
])

with tab1:
    render_tab_dictionary()

with tab2:
    render_tab_studio()

with tab3:
    render_tab_commit_lab()

with tab4:
    render_tab_library()
