"""
app.py — Audingo Songs Forge Streamlit Application.
Full NGSL Vocabulary Tracking & Song Production Pipeline.
"""

import os
import json
import datetime
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables (such as GEMINI_API_KEY)
load_dotenv()

from constants import GENRES, SONG_STRUCTURES, MOOD_CATEGORIES
import db
import pipeline
import prompt_builder
import gemini_client

# Page configuration
st.set_page_config(
    page_title="Audingo Songs Forge | NGSL Studio",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for polished look
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4F46E5, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .word-card {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        color: #0F172A !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
    }
    .word-card span, .word-card b, .word-card strong {
        color: #0F172A !important;
        font-size: 1.02rem;
    }
    .badge-noun {
        background-color: #E0E7FF !important;
        color: #1E1B4B !important;
        padding: 3px 8px !important;
        border-radius: 6px !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
    }
    .badge-verb {
        background-color: #DCFCE7 !important;
        color: #064E3B !important;
        padding: 3px 8px !important;
        border-radius: 6px !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
    }
    .badge-adj {
        background-color: #FEF3C7 !important;
        color: #78350F !important;
        padding: 3px 8px !important;
        border-radius: 6px !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
    }
    .report-card-green {
        background-color: #F0FDF4 !important;
        border: 1px solid #86EFAC !important;
        border-radius: 8px !important;
        padding: 12px !important;
        margin-bottom: 12px !important;
        color: #064E3B !important;
    }
    .report-card-green h4, .report-card-green p, .report-card-green small, .report-card-green code {
        color: #064E3B !important;
    }
    .report-card-red {
        background-color: #FEF2F2 !important;
        border: 1px solid #FCA5A5 !important;
        border-radius: 8px !important;
        padding: 12px !important;
        margin-bottom: 12px !important;
        color: #7F1D1D !important;
    }
    .report-card-red h4, .report-card-red p, .report-card-red small, .report-card-red code {
        color: #7F1D1D !important;
    }
    .report-card-blue {
        background-color: #EFF6FF !important;
        border: 1px solid #93C5FD !important;
        border-radius: 8px !important;
        padding: 12px !important;
        margin-bottom: 12px !important;
        color: #1E3A8A !important;
    }
    .report-card-blue h4, .report-card-blue p, .report-card-blue small, .report-card-blue code {
        color: #1E3A8A !important;
    }
    .report-card-yellow {
        background-color: #FEFCE8 !important;
        border: 1px solid #FDE047 !important;
        border-radius: 8px !important;
        padding: 12px !important;
        margin-bottom: 12px !important;
        color: #713F12 !important;
    }
    .report-card-yellow h4, .report-card-yellow p, .report-card-yellow small, .report-card-yellow code {
        color: #713F12 !important;
    }
    .lyrics-box {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        padding: 16px 20px !important;
        font-family: monospace !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
        white-space: pre-wrap !important;
        margin-top: 10px !important;
        margin-bottom: 12px !important;
    }
    .song-meta-bar {
        display: flex !important;
        flex-wrap: wrap !important;
        justify-content: space-between !important;
        align-items: center !important;
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.75)) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: 12px !important;
        padding: 10px 16px !important;
        margin-bottom: 14px !important;
        gap: 10px !important;
    }
    .song-time-tag {
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        font-size: 0.85rem !important;
        color: #94A3B8 !important;
        font-weight: 500 !important;
    }
    .song-time-tag b {
        color: #F1F5F9 !important;
        font-weight: 600 !important;
    }
    .song-stats-group {
        display: inline-flex !important;
        flex-wrap: wrap !important;
        align-items: center !important;
        gap: 8px !important;
    }
    .stat-badge {
        display: inline-flex !important;
        align-items: center !important;
        gap: 5px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        padding: 4px 12px !important;
        border-radius: 20px !important;
        letter-spacing: 0.2px !important;
    }
    .stat-badge-total-new {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.22) 0%, rgba(6, 182, 212, 0.22) 100%) !important;
        color: #A7F3D0 !important;
        border: 1px solid rgba(52, 211, 153, 0.5) !important;
        font-weight: 700 !important;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.25) !important;
    }
    .stat-badge-target {
        background: rgba(16, 185, 129, 0.15) !important;
        color: #34D399 !important;
        border: 1px solid rgba(52, 211, 153, 0.35) !important;
    }
    .stat-badge-bonus {
        background: rgba(59, 130, 246, 0.15) !important;
        color: #60A5FA !important;
        border: 1px solid rgba(96, 165, 250, 0.35) !important;
    }
    .stat-badge-reused {
        background: rgba(148, 163, 184, 0.15) !important;
        color: #CBD5E1 !important;
        border: 1px solid rgba(203, 213, 225, 0.28) !important;
    }
    .stat-badge-extra {
        background: rgba(245, 158, 11, 0.15) !important;
        color: #FBBF24 !important;
        border: 1px solid rgba(251, 191, 36, 0.35) !important;
    }
    .target-pill {
        display: inline-block !important;
        background: rgba(139, 92, 246, 0.15) !important;
        color: #C4B5FD !important;
        border: 1px solid rgba(167, 139, 250, 0.3) !important;
        padding: 3px 10px !important;
        border-radius: 12px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        margin: 2px 4px !important;
    }
    .bonus-pill {
        display: inline-block !important;
        background: rgba(59, 130, 246, 0.15) !important;
        color: #93C5FD !important;
        border: 1px solid rgba(96, 165, 250, 0.3) !important;
        padding: 3px 10px !important;
        border-radius: 12px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        margin: 2px 4px !important;
    }
    .extra-pill {
        display: inline-block !important;
        background: rgba(245, 158, 11, 0.15) !important;
        color: #FDE047 !important;
        border: 1px solid rgba(251, 191, 36, 0.3) !important;
        padding: 3px 10px !important;
        border-radius: 12px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        margin: 2px 4px !important;
    }
    .reused-pill {
        display: inline-block !important;
        background: rgba(148, 163, 184, 0.15) !important;
        color: #E2E8F0 !important;
        border: 1px solid rgba(148, 163, 184, 0.28) !important;
        padding: 3px 10px !important;
        border-radius: 12px !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        margin: 2px 4px !important;
    }

    /* Modern Catchy Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B0F19 0%, #111827 50%, #0F172A 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
    }
    
    .sb-brand-hero {
        background: linear-gradient(135deg, rgba(79, 70, 229, 0.18) 0%, rgba(6, 182, 212, 0.14) 100%);
        border: 1px solid rgba(99, 102, 241, 0.35);
        border-radius: 16px;
        padding: 18px 14px 14px 14px;
        margin-bottom: 16px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
    }
    .sb-brand-hero::before {
        content: "";
        position: absolute;
        top: -25px;
        left: 50%;
        transform: translateX(-50%);
        width: 140px;
        height: 55px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.45) 0%, transparent 70%);
        pointer-events: none;
    }
    .sb-logo-icon {
        font-size: 2rem;
        display: inline-block;
        margin-bottom: 4px;
        filter: drop-shadow(0 2px 10px rgba(99, 102, 241, 0.6));
    }
    .sb-title {
        font-size: 1.25rem;
        font-weight: 800;
        letter-spacing: -0.3px;
        background: linear-gradient(90deg, #C7D2FE, #38BDF8, #A78BFA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
        line-height: 1.2;
    }
    .sb-badge {
        display: inline-block;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        padding: 3px 9px;
        border-radius: 20px;
        background: rgba(99, 102, 241, 0.25);
        color: #C7D2FE;
        border: 1px solid rgba(165, 180, 252, 0.35);
        margin-bottom: 8px;
    }
    .sb-subtitle {
        font-size: 0.78rem;
        color: #94A3B8;
        line-height: 1.4;
        margin: 0;
    }
    
    /* Progress Card */
    .sb-progress-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 14px;
        padding: 13px 14px;
        margin-bottom: 14px;
        backdrop-filter: blur(8px);
    }
    .sb-progress-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .sb-progress-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: #F1F5F9;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .sb-progress-pct {
        font-size: 1.02rem;
        font-weight: 800;
        color: #34D399;
        font-family: monospace;
    }
    .sb-progress-bar-bg {
        width: 100%;
        height: 8px;
        background: rgba(51, 65, 85, 0.75);
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 8px;
    }
    .sb-progress-bar-fill {
        height: 100%;
        border-radius: 10px;
        background: linear-gradient(90deg, #6366F1 0%, #06B6D4 50%, #10B981 100%);
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
        transition: width 0.6s ease;
    }
    .sb-progress-caption {
        font-size: 0.75rem;
        color: #94A3B8;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* 2x2 Metric Grid */
    .sb-stat-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 9px;
        margin-bottom: 14px;
    }
    .sb-stat-tile {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 12px;
        padding: 11px 8px;
        text-align: center;
        transition: all 0.22s ease;
        position: relative;
        backdrop-filter: blur(6px);
    }
    .sb-stat-tile:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 14px rgba(0, 0, 0, 0.35);
    }
    .sb-stat-tile-indigo {
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    .sb-stat-tile-indigo:hover {
        border-color: rgba(129, 140, 248, 0.6);
        background: rgba(99, 102, 241, 0.14);
    }
    .sb-stat-tile-green {
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .sb-stat-tile-green:hover {
        border-color: rgba(52, 211, 153, 0.6);
        background: rgba(16, 185, 129, 0.14);
    }
    .sb-stat-tile-amber {
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .sb-stat-tile-amber:hover {
        border-color: rgba(251, 191, 36, 0.6);
        background: rgba(245, 158, 11, 0.14);
    }
    .sb-stat-tile-purple {
        border: 1px solid rgba(168, 85, 247, 0.3);
    }
    .sb-stat-tile-purple:hover {
        border-color: rgba(192, 132, 252, 0.6);
        background: rgba(168, 85, 247, 0.14);
    }
    .sb-tile-icon {
        font-size: 1.05rem;
        margin-bottom: 2px;
    }
    .sb-tile-val {
        font-size: 1.28rem;
        font-weight: 800;
        letter-spacing: -0.4px;
        line-height: 1.15;
        margin-bottom: 2px;
    }
    .sb-tile-val-indigo { color: #A5B4FC; }
    .sb-tile-val-green { color: #34D399; }
    .sb-tile-val-amber { color: #FBBF24; }
    .sb-tile-val-purple { color: #C084FC; }
    .sb-tile-label {
        font-size: 0.7rem;
        font-weight: 700;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        margin-bottom: 1px;
    }
    .sb-tile-sub {
        font-size: 0.66rem;
        color: #64748B;
    }

    /* Songs Library Mini Banner */
    .sb-songs-banner {
        background: linear-gradient(135deg, rgba(236, 72, 153, 0.12) 0%, rgba(139, 92, 246, 0.12) 100%);
        border: 1px solid rgba(236, 72, 153, 0.3);
        border-radius: 12px;
        padding: 9px 13px;
        margin-bottom: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
    }
    .sb-songs-banner:hover {
        border-color: rgba(236, 72, 153, 0.55);
        transform: translateY(-1px);
    }
    .sb-songs-info {
        display: flex;
        align-items: center;
        gap: 7px;
    }
    .sb-songs-text {
        font-size: 0.82rem;
        font-weight: 700;
        color: #F472B6;
    }
    .sb-songs-count {
        background: rgba(236, 72, 153, 0.22);
        color: #FDF2F8;
        font-size: 0.76rem;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 10px;
        border: 1px solid rgba(244, 114, 182, 0.35);
    }

    /* AI Status Pill */
    .sb-ai-status-active {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.15) 100%);
        border: 1px solid rgba(52, 211, 153, 0.32);
        border-radius: 12px;
        padding: 9px 13px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }
    .sb-pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #10B981;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 10px #10B981;
        animation: pulseDot 2s infinite;
        margin-right: 6px;
    }
    @keyframes pulseDot {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1.1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    .sb-ai-label {
        font-size: 0.8rem;
        font-weight: 700;
        color: #6EE7B7;
    }
    .sb-ai-model-tag {
        font-size: 0.68rem;
        font-weight: 700;
        background: rgba(16, 185, 129, 0.2);
        color: #A7F3D0;
        padding: 2px 7px;
        border-radius: 8px;
        border: 1px solid rgba(52, 211, 153, 0.35);
    }
</style>
""", unsafe_allow_html=True)


# Initialize SQLite DB
db.init_db()


def format_cairo_display_time(raw_ts: str) -> str:
    """Format raw timestamp into an elegant modern date & time string."""
    if not raw_ts:
        return ""
    try:
        clean_ts = str(raw_ts).replace("T", " ")
        dt = datetime.datetime.fromisoformat(clean_ts)
        return dt.strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return str(raw_ts)


def render_copy_words_toolbar(words: list[str]):
    """Renders a sleek, modern one-click copy toolbar for active target words."""
    if not words:
        return

    words_count = len(words)
    words_csv = ", ".join(words)
    words_list = "\n".join(words)
    words_csv_json = json.dumps(words_csv)
    words_list_json = json.dumps(words_list)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
      * {{
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      }}
      body, html {{
        background: transparent;
        overflow: hidden;
        height: 100%;
        display: flex;
        justify-content: flex-end;
        align-items: center;
      }}
      .toolbar-wrap {{
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 2px;
      }}
      .copy-btn {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 7px;
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: #FFFFFF;
        border: 1px solid rgba(255, 255, 255, 0.25);
        padding: 7px 15px;
        border-radius: 9px;
        font-size: 0.86rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 8px rgba(79, 70, 229, 0.28);
        outline: none;
        user-select: none;
        white-space: nowrap;
        text-decoration: none;
      }}
      .copy-btn:hover {{
        background: linear-gradient(135deg, #4338CA 0%, #6D28D9 100%);
        box-shadow: 0 4px 14px rgba(79, 70, 229, 0.42);
        transform: translateY(-1px);
      }}
      .copy-btn:active {{
        transform: translateY(0) scale(0.97);
      }}
      .copy-btn.copied {{
        background: linear-gradient(135deg, #059669 0%, #10B981 100%) !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.45) !important;
        border-color: rgba(52, 211, 153, 0.5) !important;
      }}
      .copy-btn-secondary {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
        background: #FFFFFF;
        color: #334155;
        border: 1px solid #CBD5E1;
        padding: 7px 12px;
        border-radius: 9px;
        font-size: 0.82rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
        outline: none;
        user-select: none;
        white-space: nowrap;
      }}
      .copy-btn-secondary:hover {{
        background: #F8FAFC;
        color: #0F172A;
        border-color: #94A3B8;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.12);
        transform: translateY(-1px);
      }}
      .copy-btn-secondary:active {{
        transform: translateY(0) scale(0.97);
      }}
      .copy-btn-secondary.copied {{
        background: #ECFDF5 !important;
        color: #065F46 !important;
        border-color: #34D399 !important;
        box-shadow: 0 2px 10px rgba(16, 185, 129, 0.25) !important;
      }}
      .badge-pill {{
        background: rgba(255, 255, 255, 0.22);
        font-size: 0.72rem;
        font-weight: 700;
        padding: 1px 6px;
        border-radius: 10px;
      }}
      .icon {{
        flex-shrink: 0;
        transition: transform 0.2s ease;
      }}
      .copy-btn:hover .icon, .copy-btn-secondary:hover .icon {{
        transform: scale(1.1);
      }}
    </style>
    </head>
    <body>
    <div class="toolbar-wrap">
      <button id="copy-csv-btn" class="copy-btn" onclick="copyWords('csv')" title="Copy words separated by commas">
        <svg class="icon" viewBox="0 0 24 24" width="15" height="15" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
        <span id="csv-label">Copy {words_count} Words</span>
        <span class="badge-pill">CSV</span>
      </button>

      <button id="copy-list-btn" class="copy-btn-secondary" onclick="copyWords('list')" title="Copy words one per line">
        <svg class="icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <line x1="8" y1="6" x2="21" y2="6"></line>
          <line x1="8" y1="12" x2="21" y2="12"></line>
          <line x1="8" y1="18" x2="21" y2="18"></line>
          <line x1="3" y1="6" x2="3.01" y2="6"></line>
          <line x1="3" y1="12" x2="3.01" y2="12"></line>
          <line x1="3" y1="18" x2="3.01" y2="18"></line>
        </svg>
        <span id="list-label">As List</span>
      </button>
    </div>

    <script>
      const wordsCSV = {words_csv_json};
      const wordsList = {words_list_json};

      function copyWords(mode) {{
        const text = mode === 'csv' ? wordsCSV : wordsList;
        const btn = document.getElementById(mode === 'csv' ? 'copy-csv-btn' : 'copy-list-btn');
        const label = document.getElementById(mode === 'csv' ? 'csv-label' : 'list-label');
        const origText = label.textContent;

        function indicateSuccess() {{
          btn.classList.add('copied');
          label.textContent = mode === 'csv' ? '✅ Copied {words_count} Words!' : '✅ Copied List!';
          setTimeout(() => {{
            btn.classList.remove('copied');
            label.textContent = origText;
          }}, 2200);
        }}

        if (navigator.clipboard && navigator.clipboard.writeText) {{
          navigator.clipboard.writeText(text)
            .then(indicateSuccess)
            .catch(() => fallback(text, indicateSuccess));
        }} else {{
          fallback(text, indicateSuccess);
        }}
      }}

      function fallback(text, onSuccess) {{
        try {{
          if (window.parent && window.parent.navigator && window.parent.navigator.clipboard) {{
            window.parent.navigator.clipboard.writeText(text)
              .then(onSuccess)
              .catch(() => execCopy(text, onSuccess));
            return;
          }}
        }} catch(e) {{}}
        execCopy(text, onSuccess);
      }}

      function execCopy(text, onSuccess) {{
        try {{
          const el = document.createElement('textarea');
          el.value = text;
          el.setAttribute('readonly', '');
          el.style.position = 'fixed';
          el.style.left = '-9999px';
          el.style.top = '-9999px';
          document.body.appendChild(el);
          el.focus();
          el.select();
          const res = document.execCommand('copy');
          document.body.removeChild(el);
          if (res) onSuccess();
        }} catch(err) {{
          console.error('Copy fallback failed:', err);
        }}
      }}
    </script>
    </body>
    </html>
    """
    components.html(html_code, height=44, scrolling=False)


# Cached spaCy loader
@st.cache_resource(show_spinner="Loading NLP Models...")
def load_nlp():
    import spacy
    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        from spacy.cli import download
        download("en_core_web_sm")
        return spacy.load("en_core_web_sm")


nlp = load_nlp()

# Load active studio session state from SQLite (persists across F5 browser refreshes)
persisted_session = db.load_active_batch_state()

# Session State Initialization
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
            vocalist=st.session_state.get("selected_vocalist", "Male")
        )
    else:
        db.clear_active_batch_state()


# Sidebar info
with st.sidebar:
    stats = db.get_progress_stats()
    songs_df = db.get_all_songs()
    songs_count = len(songs_df) if songs_df is not None else 0
    pct = stats.get("percent", 0.0)
    api_key_set = bool(os.environ.get("GEMINI_API_KEY"))

    # 1. Brand Hero Header
    st.markdown(
        """
        <div class="sb-brand-hero">
            <div class="sb-logo-icon">🎙️</div>
            <div class="sb-title">Audingo Songs Forge</div>
            <div class="sb-badge">NGSL STUDIO • v1.2 PRO</div>
            <p class="sb-subtitle">AI-Powered Vocabulary Targeting & Pedagogical Songwriting Engine</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. Mastery Progress Widget
    st.markdown(
        f"""
        <div class="sb-progress-card">
            <div class="sb-progress-header">
                <span class="sb-progress-title">🎯 NGSL Mastery</span>
                <span class="sb-progress-pct">{pct:.1f}%</span>
            </div>
            <div class="sb-progress-bar-bg">
                <div class="sb-progress-bar-fill" style="width: {min(pct, 100):.1f}%;"></div>
            </div>
            <div class="sb-progress-caption">
                <span><b>{stats['used']:,}</b> of {stats['total']:,} Words</span>
                <span style="color: #38BDF8; font-weight: 700;">Level {int(pct // 10) + 1}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3. 2x2 Catchy Metric Tiles
    st.markdown(
        f"""
        <div class="sb-stat-grid">
            <div class="sb-stat-tile sb-stat-tile-indigo">
                <div class="sb-tile-icon">📚</div>
                <div class="sb-tile-val sb-tile-val-indigo">{stats['total']:,}</div>
                <div class="sb-tile-label">Vocabulary</div>
                <div class="sb-tile-sub">Total NGSL</div>
            </div>
            <div class="sb-stat-tile sb-stat-tile-green">
                <div class="sb-tile-icon">🎯</div>
                <div class="sb-tile-val sb-tile-val-green">{stats['used']:,}</div>
                <div class="sb-tile-label">Mastered</div>
                <div class="sb-tile-sub">In Songs ({pct:.1f}%)</div>
            </div>
            <div class="sb-stat-tile sb-stat-tile-amber">
                <div class="sb-tile-icon">💎</div>
                <div class="sb-tile-val sb-tile-val-amber">{stats['unused']:,}</div>
                <div class="sb-tile-label">Unused</div>
                <div class="sb-tile-sub">Ready to Forge</div>
            </div>
            <div class="sb-stat-tile sb-stat-tile-purple">
                <div class="sb-tile-icon">✨</div>
                <div class="sb-tile-val sb-tile-val-purple">{stats['extra_count']:,}</div>
                <div class="sb-tile-label">Extra Hits</div>
                <div class="sb-tile-sub">Rich Discovery</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 4. Songs Produced Counter Banner
    st.markdown(
        f"""
        <div class="sb-songs-banner">
            <div class="sb-songs-info">
                <span style="font-size: 1.15rem;">🎵</span>
                <span class="sb-songs-text">Crafted Songs Vault</span>
            </div>
            <span class="sb-songs-count">{songs_count} Songs</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 5. AI Engine Status
    if api_key_set:
        st.markdown(
            """
            <div class="sb-ai-status-active">
                <div style="display: flex; align-items: center;">
                    <span class="sb-pulse-dot"></span>
                    <span class="sb-ai-label">Gemini AI Engine</span>
                </div>
                <span class="sb-ai-model-tag">ONLINE</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 10px 14px; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center;">
                    <span style="margin-right: 6px;">⚠️</span>
                    <span style="font-size: 0.82rem; font-weight: 700; color: #FBBF24;">API Key Missing</span>
                </div>
                <span style="font-size: 0.7rem; font-weight: 700; background: rgba(245, 158, 11, 0.2); color: #FDE68A; padding: 2px 7px; border-radius: 8px;">CHECK .ENV</span>
            </div>
            """,
            unsafe_allow_html=True
        )


# Header
st.markdown('<div class="main-header">Audingo Songs Forge</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">NGSL Vocabulary Targeting, AI Prompt Crafting, and Lyric Review Pipeline</div>', unsafe_allow_html=True)

# 4 Primary Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dictionary & Analytics",
    "🎧 Studio (Word Selection & Prompt)",
    "🧪 Commit Lab (Review & Approval)",
    "🎵 Songs Library"
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: DICTIONARY & ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("📚 Vocabulary Coverage & Dictionary Status")
    
    stats = db.get_progress_stats()
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("Total NGSL Headwords", f"{stats['total']:,}")
    with col_stat2:
        st.metric("Words Used in Songs", f"{stats['used']:,}", delta=f"{stats['percent']}%")
    with col_stat3:
        st.metric("Remaining Unused", f"{stats['unused']:,}")
    with col_stat4:
        st.metric("Extra Discovered Words", f"{stats['extra_count']:,}")

    # Progress bar
    fraction = (stats['used'] / stats['total']) if stats['total'] > 0 else 0.0
    st.progress(fraction, text=f"Coverage Progress: {stats['used']} / {stats['total']} words ({stats['percent']}%)")

    st.markdown("---")
    
    # Tables
    col_ngsl, col_extra = st.columns([1.3, 1])
    
    with col_ngsl:
        st.markdown("#### 📖 NGSL Dictionary")
        ngsl_df = db.get_all_ngsl_words()
        
        if not ngsl_df.empty:
            # Add Status column
            ngsl_df["Status"] = ngsl_df["usage_count"].apply(lambda c: "✅ Used" if c > 0 else "⏳ Unused")
            
            # Filters
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                pos_filter = st.selectbox("Filter POS", ["All", "Noun", "Verb", "Adjective", "Other"])
            with f_col2:
                status_filter = st.selectbox("Filter Status", ["All", "Used", "Unused"])
            with f_col3:
                search_word = st.text_input("Search Word", placeholder="Type word...")

            filtered_df = ngsl_df.copy()
            if pos_filter != "All":
                filtered_df = filtered_df[filtered_df["pos_type"] == pos_filter]
            if status_filter == "Used":
                filtered_df = filtered_df[filtered_df["usage_count"] > 0]
            elif status_filter == "Unused":
                filtered_df = filtered_df[filtered_df["usage_count"] == 0]
            if search_word:
                filtered_df = filtered_df[filtered_df["word"].str.contains(search_word.strip().lower(), case=False, na=False)]

            st.dataframe(
                filtered_df[["word", "pos_type", "Status", "usage_count", "lemma_family"]],
                column_config={
                    "word": "Headword",
                    "pos_type": "POS Type",
                    "Status": "Status",
                    "usage_count": "Times Used",
                    "lemma_family": "Lemma Family (Inflected Forms)"
                },
                use_container_width=True,
                height=480
            )
        else:
            st.info("Database is empty. Please run `python build_db.py` to ingest the vocabulary.")

    with col_extra:
        st.markdown("#### 🌟 Extra Words (Non-NGSL In Approved Songs)")
        extra_df = db.get_extra_words()
        if not extra_df.empty:
            st.dataframe(
                extra_df[["word", "occurrence_count", "first_seen_in_song"]],
                column_config={
                    "word": "Extra Word",
                    "occurrence_count": "Total Occurrences",
                    "first_seen_in_song": "First Seen In"
                },
                use_container_width=True,
                height=480
            )
        else:
            st.info("No extra words tracked yet. They will automatically appear when songs are approved in Commit Lab.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: STUDIO (WORD SELECTION & PROMPT GENERATION)
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("🎯 Target Word Selection & AI Prompt Generator")

    # ─── Approved Session Drafts — Recovery Dropdown ───────────────────────────────────
    _all_drafts = db.list_studio_drafts()
    if _all_drafts:
        with st.expander("📂 Load from Approved Session Drafts (last 10)", expanded=False):
            st.caption(
                "These snapshots were saved automatically each time you approved a song. "
                "Load one to restore its word batch and re-use it as a starting point."
            )
            _draft_options = {
                f"🎵 \u2018{d['song_title']}\u2019 — {d['label']} ({d['saved_at'][:16]})": d['id']
                for d in _all_drafts
            }
            _selected_label = st.selectbox(
                "Select a draft to preview or load:",
                options=list(_draft_options.keys()),
                index=0,
                key="draft_selector"
            )
            _selected_draft_id = _draft_options[_selected_label]

            _draft_payload = db.load_studio_draft(_selected_draft_id)
            _draft_batch = _draft_payload.get("target_batch", [])

            if _draft_batch:
                st.markdown(
                    "**Words in this draft:** " +
                    " ".join(
                        f"`{w['word']}`" for w in _draft_batch
                    )
                )

            _dc1, _dc2, _dc3 = st.columns([2, 2, 1])
            with _dc1:
                if st.button("♻️ Load Draft (words only)", use_container_width=True, key="btn_load_draft_words"):
                    if _draft_batch:
                        st.session_state.target_batch = _draft_batch
                        st.session_state.mood_analysis = None
                        st.session_state.master_prompt = ""
                        st.session_state.studio_suno_prompt = ""
                        st.session_state.studio_poster_prompt = ""
                        st.session_state.custom_concept = ""
                        sync_active_session()
                        st.success("✅ Word batch restored from draft!")
                        st.rerun()
                    else:
                        st.warning("This draft has no words saved.")
            with _dc2:
                if st.button("📦 Load Draft (full session)", use_container_width=True, key="btn_load_draft_full"):
                    if _draft_payload:
                        st.session_state.target_batch = _draft_batch
                        st.session_state.mood_analysis = _draft_payload.get("mood_analysis", None)
                        st.session_state.master_prompt = _draft_payload.get("master_prompt", "")
                        st.session_state.studio_suno_prompt = _draft_payload.get("suno_prompt", "")
                        st.session_state.studio_poster_prompt = _draft_payload.get("poster_prompt", "")
                        st.session_state.custom_concept = _draft_payload.get("custom_concept", "")
                        st.session_state.selected_genre = _draft_payload.get("selected_genre", st.session_state.selected_genre)
                        st.session_state.selected_structure = _draft_payload.get("selected_structure", st.session_state.selected_structure)
                        st.session_state.selected_vocalist = _draft_payload.get("selected_vocalist", st.session_state.selected_vocalist)
                        sync_active_session()
                        st.success("✅ Full session restored from draft!")
                        st.rerun()
                    else:
                        st.warning("Could not load this draft.")
            with _dc3:
                if st.button("🗑️ Delete", use_container_width=True, key="btn_delete_draft"):
                    db.delete_studio_draft(_selected_draft_id)
                    st.success("Draft deleted.")
                    st.rerun()


    col_actions, col_status = st.columns([2.5, 1])
    with col_actions:
        b_col1, b_col2, b_col3, b_col4 = st.columns([1.1, 1.3, 1, 0.9])
        with b_col1:
            if st.button("🎲 Random 20", type="secondary", use_container_width=True, help="Randomly pull 20 unused words (10 N, 6 V, 4 A) directly from SQLite."):
                new_batch = db.pull_20_words()
                if len(new_batch) == 20:
                    st.session_state.target_batch = new_batch
                    st.session_state.mood_analysis = None
                    st.session_state.master_prompt = ""
                    st.session_state.studio_suno_prompt = ""
                    st.session_state.custom_concept = ""
                    sync_active_session()
                    st.success("Pulled 20 random unused words (10 Nouns, 6 Verbs, 4 Adjectives)!")
                    st.rerun()
                elif len(new_batch) > 0:
                    st.session_state.target_batch = new_batch
                    st.session_state.custom_concept = ""
                    st.session_state.studio_suno_prompt = ""
                    sync_active_session()
                    st.warning(f"Only {len(new_batch)} unused words available in database.")
                    st.rerun()
                else:
                    st.error("No unused words remaining in the database!")

        with b_col2:
            if st.button("🧠 Smart Thematic Pull", type="primary", use_container_width=True, help="Gemini analyzes 140 candidate unused words and selects 20 words (10 N, 6 V, 4 A) that share natural chemistry and relate to an authentic everyday life scenario."):
                with st.spinner("🧠 Gemini is curating a cohesive 20-word batch from 140 candidate unused words..."):
                    candidate_pool = db.pull_candidate_pool_for_thematic_curation(nouns_limit=70, verbs_limit=40, adjs_limit=30)
                    candidate_nouns = [w["word"] for w in candidate_pool["Noun"]]
                    candidate_verbs = [w["word"] for w in candidate_pool["Verb"]]
                    candidate_adjs = [w["word"] for w in candidate_pool["Adjective"]]
                    
                    curation_res = gemini_client.curate_thematic_vocabulary_batch(
                        candidate_nouns=candidate_nouns,
                        candidate_verbs=candidate_verbs,
                        candidate_adjs=candidate_adjs
                    )
                    
                    curated_batch = db.build_curated_batch_from_words(
                        selected_nouns=curation_res.get("selected_nouns", []),
                        selected_verbs=curation_res.get("selected_verbs", []),
                        selected_adjs=curation_res.get("selected_adjectives", []),
                        candidate_pool=candidate_pool
                    )
                    
                    if len(curated_batch) == 20:
                        st.session_state.target_batch = curated_batch
                        st.session_state.mood_analysis = None
                        st.session_state.master_prompt = ""
                        st.session_state.studio_suno_prompt = ""
                        st.session_state.custom_concept = curation_res.get("theme_description", "")
                        sync_active_session()
                        theme_title = curation_res.get("theme_name", "Curated Storyline")
                        st.success(f"✨ Curated 20 thematic words for '{theme_title}' (10 Nouns, 6 Verbs, 4 Adjectives)!")
                        st.rerun()
                    elif len(curated_batch) > 0:
                        st.session_state.target_batch = curated_batch
                        st.session_state.custom_concept = curation_res.get("theme_description", "")
                        sync_active_session()
                        st.warning(f"Curated {len(curated_batch)} words.")
                        st.rerun()
                    else:
                        st.error("Could not curate a batch from unused words.")

        with b_col3:
            if st.button("🔄 Cancel & Redraw", use_container_width=True):
                new_batch = db.pull_20_words()
                st.session_state.target_batch = new_batch
                st.session_state.mood_analysis = None
                st.session_state.master_prompt = ""
                st.session_state.studio_suno_prompt = ""
                st.session_state.custom_concept = ""
                sync_active_session()
                st.info("Batch redrawn.")
                st.rerun()

        with b_col4:
            if st.button("🧹 Clear", use_container_width=True, help="Clear active target batch"):
                st.session_state.target_batch = []
                st.session_state.mood_analysis = None
                st.session_state.master_prompt = ""
                st.session_state.studio_suno_prompt = ""
                st.session_state.custom_concept = ""
                db.clear_active_batch_state()
                st.rerun()

    # Display Active Batch
    if st.session_state.target_batch:
        current_words = [w["word"] for w in st.session_state.target_batch]
        current_ids = [w["id"] for w in st.session_state.target_batch]
        
        # Breakdown counters
        nouns_count = sum(1 for w in st.session_state.target_batch if w["pos_type"] == "Noun")
        verbs_count = sum(1 for w in st.session_state.target_batch if w["pos_type"] == "Verb")
        adjs_count = sum(1 for w in st.session_state.target_batch if w["pos_type"] == "Adjective")
        others_count = sum(1 for w in st.session_state.target_batch if w["pos_type"] not in ("Noun", "Verb", "Adjective"))

        # Batch Header & Quick Action Toolbar
        col_batch_info, col_batch_actions = st.columns([1.25, 1.15], vertical_alignment="center")
        with col_batch_info:
            other_pill = f'<span style="background: #F1F5F9; color: #475569; font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; border: 1px solid #CBD5E1;">⚪ {others_count} Other</span>' if others_count else ''
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 2px;">
                    <span style="font-weight: 700; color: #0F172A; font-size: 1.05rem;">🎯 Active Target Batch:</span>
                    <span style="background: #EDE9FE; color: #5B21B6; font-size: 0.82rem; font-weight: 700; padding: 2px 9px; border-radius: 12px; border: 1px solid #DDD6FE;">{len(st.session_state.target_batch)} Words</span>
                    <span style="background: #E0E7FF; color: #3730A3; font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; border: 1px solid #C7D2FE;">🔵 {nouns_count} Nouns</span>
                    <span style="background: #DCFCE7; color: #166534; font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; border: 1px solid #BBF7D0;">🟢 {verbs_count} Verbs</span>
                    <span style="background: #FEF3C7; color: #92400E; font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; border: 1px solid #FDE68A;">🟡 {adjs_count} Adjectives</span>
                    {other_pill}
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_batch_actions:
            render_copy_words_toolbar(current_words)

        # 4 columns of 5 words
        cols = st.columns(4)
        for idx, word_item in enumerate(st.session_state.target_batch):
            col_target = cols[idx % 4]
            with col_target:
                pos = word_item["pos_type"]
                badge_class = "badge-noun" if pos == "Noun" else ("badge-verb" if pos == "Verb" else "badge-adj")
                
                with st.container():
                    st.markdown(
                        f"""
                        <div class="word-card">
                            <span style="color: #0F172A !important;"><strong style="color: #0F172A !important; font-size: 1.05rem;">{idx+1}. {word_item['word']}</strong></span>
                            <span class="{badge_class}">{pos}</span>
                        </div>

                        """,
                        unsafe_allow_html=True
                    )
                    # Swap button
                    if st.button(f"🔄 Swap", key=f"swap_{word_item['id']}_{idx}", help=f"Swap '{word_item['word']}' with another unused {pos}"):
                        swapped = db.swap_single_word(pos, current_ids)
                        if swapped:
                            st.session_state.target_batch[idx] = swapped
                            st.session_state.master_prompt = ""  # prompt needs regen
                            st.session_state.studio_suno_prompt = ""
                            sync_active_session()
                            st.success(f"Swapped '{word_item['word']}' → '{swapped['word']}'")
                            st.rerun()
                        else:
                            st.warning(f"No more unused {pos} words available to swap.")

        st.markdown("---")

        # Step 2: Gemini Mood & Style Analysis
        st.subheader("🤖 Step 2: Gemini Flash Mood & Musical Analysis")
        col_gem1, col_gem2 = st.columns([1.5, 2])
        
        with col_gem1:
            st.markdown("Analyze the 20 target words to get an emotional breakdown, genre, and structure.")
            if st.button("✨ Run Gemini Analysis", type="secondary", use_container_width=True):
                with st.spinner("Analyzing vocabulary mood with Gemini Flash..."):
                    res = gemini_client.analyze_vocabulary_mood(current_words)
                    st.session_state.mood_analysis = res
                    if res.get("genre"):
                        st.session_state.selected_genre = res["genre"]
                    if res.get("song_structure"):
                        st.session_state.selected_structure = res["song_structure"]
                    if res.get("creative_concept"):
                        st.session_state.custom_concept = res["creative_concept"]
                    sync_active_session()
                    st.rerun()

            if st.session_state.mood_analysis:
                analysis = st.session_state.mood_analysis
                st.success(f"Analyzed using: `{analysis.get('model_used', 'Gemini')}`")

        with col_gem2:
            if st.session_state.mood_analysis:
                analysis = st.session_state.mood_analysis
                mood_data = analysis.get("mood_breakdown", {})
                if mood_data:
                    mood_df = pd.DataFrame(list(mood_data.items()), columns=["Mood", "Percentage"])
                    mood_df = mood_df.sort_values(by="Percentage", ascending=False)
                    st.bar_chart(mood_df.set_index("Mood"), color="#4F46E5", height=220)

        # Style & Structure Selector (Initialized by Gemini, user can tweak)
        st.markdown("#### 🎛️ Tune Musical Direction & Story Concept")
        tune_col1, tune_col2, tune_col3 = st.columns([1.5, 1, 1.5])
        with tune_col1:
            default_genre_idx = GENRES.index(st.session_state.selected_genre) if st.session_state.selected_genre in GENRES else 0
            new_genre = st.selectbox("Genre (Closed List)", GENRES, index=default_genre_idx)
            if new_genre != st.session_state.selected_genre:
                st.session_state.selected_genre = new_genre
                sync_active_session()

        with tune_col2:
            voc_options = ["Male", "Female", "Duet", "Instrumental"]
            default_voc_idx = voc_options.index(st.session_state.selected_vocalist) if st.session_state.selected_vocalist in voc_options else 0
            new_voc = st.selectbox("Lead Vocalist", voc_options, index=default_voc_idx)
            if new_voc != st.session_state.selected_vocalist:
                st.session_state.selected_vocalist = new_voc
                sync_active_session()

        with tune_col3:
            default_struct_idx = SONG_STRUCTURES.index(st.session_state.selected_structure) if st.session_state.selected_structure in SONG_STRUCTURES else 0
            new_struct = st.selectbox("Song Structure (Closed List)", SONG_STRUCTURES, index=default_struct_idx)
            if new_struct != st.session_state.selected_structure:
                st.session_state.selected_structure = new_struct
                sync_active_session()

        new_concept = st.text_area(
            "💡 Story / Creative Concept (Generated by Gemini, fully editable by you):",
            value=st.session_state.custom_concept,
            height=75,
            help="Tweak Gemini's concept or write your own practical everyday life scenario before generating the prompt."
        )
        if new_concept != st.session_state.custom_concept:
            st.session_state.custom_concept = new_concept
            sync_active_session()

        # Generate Master Prompt, Suno Style Prompt & Poster Prompt
        st.markdown("---")
        st.subheader("📋 Step 3: Generation & Production Prompts")
        
        if st.button("🚀 Generate Final Prompt", type="primary", use_container_width=True):
            mood_dict = st.session_state.mood_analysis.get("mood_breakdown", {}) if st.session_state.mood_analysis else {}
            concept = st.session_state.custom_concept.strip() or (
                st.session_state.mood_analysis.get("creative_concept", "") if st.session_state.mood_analysis else ""
            )
            
            with st.spinner("🚀 Crafting Master Songwriting Prompt, Suno Style, and Poster Art Prompt..."):
                used_content_words = db.get_previously_used_words(exclude_words=current_words)
                prompt_text = prompt_builder.generate_master_prompt(
                    target_words=current_words,
                    genre=st.session_state.selected_genre,
                    song_structure=st.session_state.selected_structure,
                    mood_analysis=mood_dict,
                    creative_concept=concept,
                    previously_used_words=used_content_words
                )
                suno_text = prompt_builder.build_suno_style_prompt(
                    genre=st.session_state.selected_genre,
                    vocalist=st.session_state.selected_vocalist
                )
                poster_text = gemini_client.generate_studio_poster_prompt(
                    concept=concept,
                    genre=st.session_state.selected_genre,
                    vocalist=st.session_state.selected_vocalist,
                    title="[Song Title]"
                )
                st.session_state.master_prompt = prompt_text
                st.session_state.studio_suno_prompt = suno_text
                st.session_state.studio_poster_prompt = poster_text
                sync_active_session()

        if st.session_state.master_prompt:
            # ──────────────────────────────────────────────────────────
            # 1. Dedicated Suno AI Music Style Prompt Section
            # ──────────────────────────────────────────────────────────
            st.markdown("#### 🎵 1. Suno AI Music Style Prompt (Ready to Paste into Suno):")
            st.caption("Dense, keyword-rich Suno style prompt (< 120 chars) tailored to your selected genre, tempo, and vocal clarity:")
            
            suno_prompt_val = st.session_state.studio_suno_prompt or prompt_builder.build_suno_style_prompt(
                genre=st.session_state.selected_genre,
                vocalist=st.session_state.selected_vocalist
            )
            suno_char_len = len(suno_prompt_val)
            suno_color = "#10B981" if suno_char_len <= 120 else "#EF4444"
            st.markdown(
                f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;'>"
                f"<small style='color: #94A3B8;'>📋 Click the copy icon in the box below to paste into Suno's 'Style of Music' box</small>"
                f"<small style='color: {suno_color}; font-weight: 700;'>Length: {suno_char_len} / 120 chars</small>"
                f"</div>",
                unsafe_allow_html=True
            )
            st.code(suno_prompt_val, language="markdown")

            st.markdown("<hr style='margin: 18px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

            # ──────────────────────────────────────────────────────────
            # 2. Midjourney / DALL-E Album Cover Poster Prompt Section
            # ──────────────────────────────────────────────────────────
            st.markdown("#### 🎨 2. Midjourney / DALL-E Album Cover Prompt (Poster Art):")
            st.caption("Artistic visual prompt capturing the genre aesthetic, lighting, and story atmosphere (will automatically incorporate your official song title when saved in Commit Lab):")
            
            concept_for_poster = st.session_state.custom_concept.strip() or (
                st.session_state.mood_analysis.get("creative_concept", "") if st.session_state.mood_analysis else ""
            )
            poster_prompt_val = st.session_state.studio_poster_prompt or gemini_client.generate_studio_poster_prompt(
                concept=concept_for_poster,
                genre=st.session_state.selected_genre,
                vocalist=st.session_state.selected_vocalist,
                title="[Song Title]"
            )
            st.code(poster_prompt_val, language="markdown")

            st.markdown("<hr style='margin: 18px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

            # ──────────────────────────────────────────────────────────
            # 3. Master Songwriting Prompt Section
            # ──────────────────────────────────────────────────────────
            st.markdown("#### 📝 3. Master Lyrics Prompt (Copy & Paste into Claude / GPT-4o):")
            st.caption("Full prompt containing all 20 target vocabulary words, real-world narrative concept, and strict Logic Gate:")
            st.code(st.session_state.master_prompt, language="markdown")
    else:
        st.info("👉 Click **[Pull 20 Words]** above to select a batch of 20 unused words and begin.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: COMMIT LAB (REVIEW & APPROVAL)
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("🧪 Song Review, Text Pipeline & Word Approval")
    
    # Show commit success banner if a song was just saved
    if st.session_state.get("commit_success_message"):
        msg = st.session_state.commit_success_message
        st.balloons()
        song_num = msg.get("song_number")
        num_label = f"Song #{song_num}" if song_num else f"Song #{msg.get('song_id')}"
        st.success(
            f"🎉 **Song '{msg['title']}' Saved Successfully as {num_label}!**\n\n"
            f"- 🟢 **Target Words Approved:** {msg.get('target_count', 0)} words\n"
            f"- 🔵 **New Bonus NGSL Hits:** {msg.get('bonus_count', 0)} words (first time covered)\n"
            f"- ⚪ **Previously Covered Words Reused:** {msg.get('reused_count', 0)} words (usage counters incremented)\n"
            f"- 🟡 **Extra Non-NGSL Words:** {msg.get('extra_count', 0)} words\n\n"
            f"📊 **Progress Update:** **{msg['unused_remaining']:,}** words remain unused in NGSL (**{msg.get('total_used', 0):,}** words covered total)."
        )
        st.session_state.commit_success_message = None

    # Show active target words reminder
    if st.session_state.target_batch:
        current_target_words = [w["word"] for w in st.session_state.target_batch]
        target_display = ", ".join(f"`{w}`" for w in current_target_words)
        st.markdown(f"**Current 20 Target Words from Studio:** {target_display}")
    else:
        st.warning("⚠️ No active target batch loaded from Studio. If you analyze a song now, all detected NGSL words will be classified as Bonus hits (Blue), not Target hits (Green).")
        current_target_words = []

    st.markdown("Paste the final song lyrics generated by Suno AI / external LLM:")
    
    # ── Song Title with Mandatory Validation, Red Highlight & Auto-Focus ──
    has_title_error = st.session_state.get("title_has_error", False) and not (st.session_state.song_title_input or "").strip()

    title_label = "🎵 Song Title *(Required before approval)*" if has_title_error else "🎵 Song Title"
    
    st.session_state.song_title_input = st.text_input(
        title_label,
        value=st.session_state.song_title_input,
        placeholder="e.g. Echoes of the Horizon (Required to Approve & Save)",
        key="commit_song_title_input_field"
    )
    if st.session_state.song_title_input.strip() and st.session_state.get("title_has_error"):
        st.session_state.title_has_error = False

    if has_title_error:
        st.markdown(
            """
            <div id="title-error-banner" style="
                background: rgba(239, 68, 68, 0.12);
                border: 1px solid rgba(239, 68, 68, 0.4);
                border-radius: 8px;
                padding: 9px 14px;
                color: #EF4444;
                font-size: 0.88rem;
                font-weight: 700;
                margin-top: -6px;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                gap: 8px;
            ">
                <span style="font-size: 1.15rem;">⚠️</span>
                <span>لا يمكن اعتماد الأغنية بدون عنوان! يرجى كتابة عنوان الأغنية هنا أولاً (Song Title is required).</span>
            </div>
            <style>
            div[data-testid="stTextInput"]:has(input[aria-label*="Song Title"]) input,
            div[data-testid="stTextInput"]:has(input[placeholder*="Echoes"]) input {
                border: 2px solid #EF4444 !important;
                background-color: rgba(239, 68, 68, 0.08) !important;
                box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.28) !important;
                animation: pulseTitleError 1.5s infinite alternate !important;
            }
            @keyframes pulseTitleError {
                from { box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.2); }
                to { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0.45); }
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        # Automatically scroll viewport and focus cursor directly into Song Title
        components.html(
            """
            <script>
            setTimeout(() => {
                try {
                    const doc = window.parent.document;
                    const el = doc.querySelector('input[aria-label*="Song Title"]') || doc.querySelector('input[placeholder*="Echoes"]');
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        el.focus();
                        el.select();
                    }
                } catch(e) {
                    console.error("Focus error:", e);
                }
            }, 100);
            </script>
            """,
            height=0,
            width=0
        )
    
    st.session_state.raw_lyrics_input = st.text_area(
        "Song Lyrics",
        value=st.session_state.raw_lyrics_input,
        placeholder="Paste full lyrics including [Verse], [Chorus] tags here...",
        height=260
    )

    col_btn_analyze, col_btn_clear = st.columns([1.5, 3])
    with col_btn_analyze:
        if st.button("🔍 Analyze Song", type="primary", use_container_width=True):
            if not st.session_state.raw_lyrics_input.strip():
                st.error("Please paste song lyrics before analyzing.")
            else:
                with st.spinner("Executing 5-step song processing pipeline..."):
                    lemma_map = db.get_all_lemma_mappings()
                    used_ngsl = db.get_used_ngsl_words()
                    results = pipeline.process_song_text(
                        raw_lyrics=st.session_state.raw_lyrics_input,
                        target_words=current_target_words,
                        lemma_to_headword=lemma_map,
                        nlp=nlp,
                        used_ngsl_words=used_ngsl
                    )
                    st.session_state.analysis_results = results
                    st.rerun()

    # If results are ready, show report and approval form
    if st.session_state.analysis_results:
        res = st.session_state.analysis_results
        green_list = res.get("green", [])
        red_list = res.get("red", [])
        blue_list = res.get("blue", [])
        reused_list = res.get("reused", [])
        yellow_list = res.get("yellow", [])

        st.markdown("---")
        st.subheader("📊 Color-Coded Classification Report")
        
        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
        m_col1.metric("🟢 Target Hits", f"{len(green_list)} / {len(current_target_words)}")
        m_col2.metric("🔴 Missed Targets", f"{len(red_list)}")
        m_col3.metric("🔵 Bonus Hits (New)", f"{len(blue_list)}")
        m_col4.metric("⚪ Previously Covered", f"{len(reused_list)}")
        m_col5.metric("🟡 Extra Words", f"{len(yellow_list)}")

        st.info("Uncheck any word below if you do NOT want it counted towards the database counters.")

        # Interactive form with checkboxes
        with st.form("approval_form"):
            rep_col1, rep_col2 = st.columns(2)

            # 🟢 Green & 🔴 Red
            with rep_col1:
                # Green
                st.markdown(
                    f"""
                    <div class="report-card-green">
                        <h4>🟢 Target Hits ({len(green_list)})</h4>
                        <p><small>Target words found in song → will increment <code>usage_count</code>.</small></p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                checked_green = []
                if green_list:
                    for w in green_list:
                        if st.checkbox(f"🟢 {w}", value=True, key=f"chk_green_{w}"):
                            checked_green.append(w)
                else:
                    st.caption("No target words detected in the lyrics.")

                # Red
                st.markdown(
                    f"""
                    <div class="report-card-red">
                        <h4>🔴 Missed Targets ({len(red_list)})</h4>
                        <p><small>Target words not found in song → remains <code>usage_count = 0</code>.</small></p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if not current_target_words:
                    st.caption("No target batch was active during analysis.")
                elif red_list:
                    st.markdown(", ".join(f"`{w}`" for w in red_list))
                else:
                    st.success(f"🎉 Perfect! All {len(current_target_words)} target words were used in the song!")

            # 🔵 Blue & ⚪ Reused & 🟡 Yellow
            with rep_col2:
                # Blue: New Bonus Hits
                st.markdown(
                    f"""
                    <div class="report-card-blue">
                        <h4>🔵 Bonus NGSL Hits ({len(blue_list)})</h4>
                        <p><small>New, previously unused NGSL words → will count as newly covered and increment <code>usage_count</code>.</small></p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                checked_blue = []
                if blue_list:
                    for w in blue_list:
                        if st.checkbox(f"🔵 {w}", value=True, key=f"chk_blue_{w}"):
                            checked_blue.append(w)
                else:
                    st.caption("No newly introduced NGSL words found.")

                # Reused: Previously Covered NGSL Words
                if reused_list:
                    reused_pills = " ".join(f'<span class="reused-pill">{w}</span>' for w in reused_list)
                    st.markdown(
                        f"""
                        <div style="background: rgba(148, 163, 184, 0.08); border: 1px solid rgba(148, 163, 184, 0.25); border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                            <h4 style="margin: 0 0 4px 0; color: #94A3B8;">⚪ Previously Covered Words ({len(reused_list)})</h4>
                            <p style="margin: 0 0 8px 0;"><small style="color: #64748B;">NGSL words already introduced in past songs. Their global usage counter will update upon saving, but they are not counted as new bonus discoveries.</small></p>
                            <div>{reused_pills}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # Yellow: Extra Words
                st.markdown(
                    f"""
                    <div class="report-card-yellow">
                        <h4>🟡 Extra Words ({len(yellow_list)})</h4>
                        <p><small>Valid words not in NGSL → will be added/incremented in <code>extra_words</code>.</small></p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                checked_yellow = []
                if yellow_list:
                    for w in yellow_list:
                        if st.checkbox(f"🟡 {w}", value=True, key=f"chk_yellow_{w}"):
                            checked_yellow.append(w)
                else:
                    st.caption("No extra non-NGSL words found.")

            pack_vocalist = st.session_state.get("selected_vocalist", "Male")
            st.markdown(
                f"""
                <div style="background: rgba(99, 102, 241, 0.08); border-left: 4px solid #6366F1; padding: 10px 14px; border-radius: 8px; margin: 12px 0 16px 0; font-size: 0.92rem; color: #E2E8F0;">
                    💿 <b>Packaging Integration:</b> When you approve, this song will automatically register its 
                    <b>Suno AI Music Style Prompt</b> and <b>Album Poster Prompt</b> under genre <b>{st.session_state.selected_genre}</b> ({pack_vocalist}) in your Songs Library!
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("---")
            submitted = st.form_submit_button("✅ Approve & Save Song", type="primary", use_container_width=True)
            
            if submitted:
                title = (st.session_state.song_title_input or "").strip()
                if not title:
                    st.session_state.title_has_error = True
                    st.toast("⚠️ برجاء كتابة عنوان الأغنية أولاً! تم نقلك لحقل العنوان.", icon="⚠️")
                    st.rerun()

                st.session_state.title_has_error = False

                all_ngsl_to_increment = checked_green + checked_blue
                
                # Fetch metadata to persist with song
                mood_dict = st.session_state.mood_analysis.get("mood_breakdown", {}) if st.session_state.mood_analysis else {}
                current_genre = st.session_state.selected_genre
                current_structure = st.session_state.selected_structure
                current_concept = st.session_state.custom_concept.strip() or (
                    st.session_state.mood_analysis.get("creative_concept", "") if st.session_state.mood_analysis else ""
                )

                song_id, approved_ngsl_count, approved_extra_count = db.approve_and_save_song(
                    title=title,
                    lyrics=st.session_state.raw_lyrics_input.strip(),
                    target_words=current_target_words,
                    checked_bonus_words=checked_blue,
                    checked_extra_words=checked_yellow,
                    checked_target_words=checked_green,
                    reused_words=reused_list,
                    mood_breakdown=mood_dict,
                    genre=current_genre,
                    song_structure=current_structure,
                    creative_concept=current_concept
                )

                # Auto-save track variant packaging (Suno prompt + Poster prompt) for this song
                current_vocalist = st.session_state.get("selected_vocalist", "Male")
                saved_suno = (st.session_state.get("studio_suno_prompt") or "").strip()
                if not saved_suno:
                    saved_suno = prompt_builder.build_suno_style_prompt(current_genre, current_vocalist)

                saved_poster = (st.session_state.get("studio_poster_prompt") or "").strip()
                if saved_poster:
                    saved_poster = (
                        saved_poster
                        .replace("[Song Title]", title)
                        .replace("Your Song Title", title)
                        .replace("Untitled Song", title)
                    )
                else:
                    saved_poster = gemini_client.generate_studio_poster_prompt(
                        concept=current_concept or title,
                        genre=current_genre,
                        vocalist=current_vocalist,
                        title=title
                    )

                db.save_track_variant(
                    song_id=song_id,
                    genre=current_genre,
                    vocalist=current_vocalist,
                    suno_prompt=saved_suno,
                    poster_prompt=saved_poster
                )

                new_stats = db.get_progress_stats()

                # ── Save studio draft snapshot BEFORE clearing session state ──
                db.save_studio_draft(
                    song_title=title,
                    batch=list(st.session_state.target_batch),
                    concept=current_concept,
                    genre=current_genre,
                    song_structure=current_structure,
                    mood_analysis=st.session_state.mood_analysis,
                    master_prompt=st.session_state.get("master_prompt", ""),
                    suno_prompt=st.session_state.get("studio_suno_prompt", ""),
                    poster_prompt=st.session_state.get("studio_poster_prompt", ""),
                    vocalist=current_vocalist,
                )

                # Reset batch & form
                st.session_state.target_batch = []
                st.session_state.mood_analysis = None
                st.session_state.master_prompt = ""
                st.session_state.studio_suno_prompt = ""
                st.session_state.studio_poster_prompt = ""
                st.session_state.custom_concept = ""
                st.session_state.analysis_results = None
                st.session_state.raw_lyrics_input = ""
                st.session_state.song_title_input = ""
                st.session_state.title_has_error = False
                db.clear_active_batch_state()

                # Calculate real chronological song number
                all_saved_df = db.get_all_songs()
                real_song_num = len(all_saved_df)

                # Store success message and trigger instant rerun so sidebar & tabs update reactively
                st.session_state.commit_success_message = {
                    "title": title,
                    "song_number": real_song_num,
                    "song_id": song_id,
                    "target_count": len(checked_green),
                    "bonus_count": len(checked_blue),
                    "reused_count": len(reused_list),
                    "extra_count": len(checked_yellow),
                    "unused_remaining": new_stats["unused"],
                    "total_used": new_stats["used"]
                }
                st.rerun()


@st.dialog("⚠️ Confirm Song Deletion")
def confirm_delete_song_dialog(song_id: int, song_title: str, row_num: int):
    """Safety confirmation modal before executing atomic delete and rollback."""
    st.markdown(f"#### 🗑️ Are you sure you want to delete Song #{row_num}?")
    st.warning(
        f"**Song Title:** {song_title}\n\n"
        f"⚠️ **Atomic Safe Rollback will occur:**\n"
        f"- Target & Bonus vocabulary will have their `usage_count` decremented (-1) in the NGSL dictionary.\n"
        f"- Non-NGSL extra words will have their occurrences decremented (-1).\n"
        f"- The song and all its recorded metadata will be permanently removed."
    )
    dlg_c1, dlg_c2 = st.columns(2)
    with dlg_c1:
        if st.button("🔥 Yes, Confirm Delete", type="primary", use_container_width=True, key=f"dlg_confirm_del_{song_id}"):
            if db.delete_song(song_id, rollback_words=True):
                st.session_state["lib_toast_msg"] = f"Song #{row_num} ('{song_title}') deleted and dictionary counters rolled back."
                st.rerun()
    with dlg_c2:
        if st.button("❌ Cancel", use_container_width=True, key=f"dlg_cancel_del_{song_id}"):
            st.rerun()


@st.dialog("⚠️ Confirm Track Variant Deletion")
def confirm_delete_variant_dialog(variant_id: int, genre: str, vocalist: str):
    """Safety confirmation modal before deleting a track variant package."""
    st.markdown("#### 🗑️ Delete Track Variant Package?")
    st.warning(
        f"Are you sure you want to delete the production package for **{genre}** ({vocalist})?\n\n"
        f"This will permanently delete both the Suno music prompt and the poster art prompt. This action cannot be undone."
    )
    dlg_c1, dlg_c2 = st.columns(2)
    with dlg_c1:
        if st.button("🔥 Yes, Delete Variant", type="primary", use_container_width=True, key=f"dlg_confirm_del_variant_{variant_id}"):
            if db.delete_track_variant(variant_id):
                st.session_state["lib_toast_msg"] = f"Track variant for '{genre}' ({vocalist}) was deleted."
                st.rerun()
    with dlg_c2:
        if st.button("❌ Cancel", use_container_width=True, key=f"dlg_cancel_del_variant_{variant_id}"):
            st.rerun()


@st.dialog("⚠️ Warning: Style Package Already Exists")
def confirm_overwrite_variant_dialog(song_id: int, song_title: str, lyrics_text: str, genre: str, vocalist: str):
    """Safety confirmation modal before overwriting an existing track variant."""
    st.markdown("#### ⚠️ Style Package Already Exists!")
    st.warning(
        f"A production package for **'{song_title}'** in **{genre}** with **{vocalist}** vocals already exists.\n\n"
        f"Generating a new package will **overwrite** both the current Suno music prompt and Midjourney/DALL-E poster prompt with freshly generated versions.\n\n"
        f"Are you sure you want to proceed and overwrite?"
    )
    dlg_c1, dlg_c2 = st.columns(2)
    clean_g = "".join(c for c in genre if c.isalnum())
    with dlg_c1:
        if st.button("⚡ Yes, Overwrite & Regenerate", type="primary", use_container_width=True, key=f"dlg_confirm_ovr_{song_id}_{clean_g}_{vocalist}"):
            with st.spinner(f"Generating new package for '{genre}' ({vocalist})..."):
                res = gemini_client.generate_track_variant(
                    title=song_title,
                    lyrics=lyrics_text,
                    genre=genre,
                    vocalist=vocalist
                )
                if res.get("success"):
                    new_suno_p = res.get("suno_prompt", "").strip()
                    new_poster_p = res.get("poster_prompt", "").strip()
                    db.upsert_track_variant(
                        song_id=song_id,
                        genre=genre,
                        vocalist=vocalist,
                        suno_prompt=new_suno_p,
                        poster_prompt=new_poster_p
                    )
                    st.session_state["lib_toast_msg"] = f"Track package for '{genre}' ({vocalist}) overwritten & updated!"
                    st.rerun()
                else:
                    st.error(f"Failed to generate package: {res.get('error')}")
    with dlg_c2:
        if st.button("❌ Cancel", use_container_width=True, key=f"dlg_cancel_ovr_{song_id}_{clean_g}_{vocalist}"):
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: SONGS LIBRARY & ARCHIVES
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    if "lib_toast_msg" in st.session_state:
        toast_msg = st.session_state.pop("lib_toast_msg")
        st.toast(f"💾 {toast_msg}", icon="✅")
        st.success(toast_msg)

    st.subheader("🎵 Saved Songs Library & Archives")
    st.markdown("Browse and manage all approved songs, review target vocabulary, inspect Gemini mood percentages, and edit song details.")

    songs_df = db.get_all_songs()

    if songs_df.empty:
        st.info("No songs saved yet. Head to the **Commit Lab** to analyze and approve songs to build your library!")
    else:
        # Assign chronological song number: oldest is #1, newest is #N
        songs_df = songs_df.reset_index(drop=True)
        songs_df["row_num"] = songs_df["id"].rank(method="dense", ascending=True).astype(int)

        # Metrics summary
        lib_c1, lib_c2 = st.columns([1, 2])
        with lib_c1:
            st.metric("Total Songs Saved", len(songs_df))
        with lib_c2:
            search_query = st.text_input("🔍 Search Songs", placeholder="Filter by title, lyrics, or target words...")

        filtered_df = songs_df
        if search_query.strip():
            q = search_query.strip().lower()
            filtered_df = songs_df[
                songs_df["title"].str.lower().str.contains(q, na=False) |
                songs_df["lyrics"].str.lower().str.contains(q, na=False) |
                songs_df["target_words"].str.lower().str.contains(q, na=False) |
                songs_df["bonus_words"].str.lower().str.contains(q, na=False) |
                songs_df.get("reused_words", pd.Series("", index=songs_df.index)).fillna("").str.lower().str.contains(q, na=False) |
                songs_df["extra_words"].str.lower().str.contains(q, na=False)
            ]

        st.caption(f"Showing **{len(filtered_df)}** of **{len(songs_df)}** saved songs:")

        for loop_idx, (_, row) in enumerate(filtered_df.iterrows()):
            song_id = int(row["id"])
            row_num = int(row["row_num"])
            song_title = row["title"]
            created_at = row["created_at"]
            target_words_raw = row["target_words"] or ""
            bonus_words_raw = row.get("bonus_words") or ""
            reused_words_raw = row.get("reused_words") or ""
            extra_words_raw = row.get("extra_words") or ""
            lyrics_text = row["lyrics"] or ""
            genre_val = row.get("genre") or ""
            structure_val = row.get("song_structure") or ""
            concept_val = row.get("creative_concept") or ""
            mood_raw = row.get("mood_breakdown") or ""

            target_list = [w.strip() for w in target_words_raw.split(",") if w.strip()]
            bonus_list = [w.strip() for w in bonus_words_raw.split(",") if w.strip()]
            reused_list = [w.strip() for w in reused_words_raw.split(",") if w.strip()]
            extra_list = [w.strip() for w in extra_words_raw.split(",") if w.strip()]

            # Parse mood breakdown
            mood_dict = {}
            if mood_raw:
                try:
                    mood_dict = json.loads(mood_raw) if isinstance(mood_raw, str) else mood_raw
                except Exception:
                    mood_dict = {}

            display_time = format_cairo_display_time(created_at)
            total_new_words = len(target_list) + len(bonus_list)

            with st.expander(
                f"🎵 #{row_num} — **{song_title}** ｜ 🔥 **+{total_new_words} New NGSL** (🟢 {len(target_list)} + 🔵 {len(bonus_list)}) ｜ ⚪ {len(reused_list)} Reused  🟡 {len(extra_list)} Extra ｜ 📅 {display_time}",
                expanded=(loop_idx == 0)
            ):
                # Modern Meta & Stats Header Bar
                st.markdown(
                    f"""
                    <div class="song-meta-bar">
                        <div class="song-time-tag">
                            <span>🕒</span> <span>Created: <b>{display_time}</b> <small style="color: #64748B;">(Cairo Time)</small></span>
                        </div>
                        <div class="song-stats-group">
                            <span class="stat-badge stat-badge-total-new">🔥 +{total_new_words} New NGSL</span>
                            <span class="stat-badge stat-badge-target">🟢 {len(target_list)} Targets</span>
                            <span class="stat-badge stat-badge-bonus">🔵 {len(bonus_list)} Bonus</span>
                            <span class="stat-badge stat-badge-reused">⚪ {len(reused_list)} Reused</span>
                            <span class="stat-badge stat-badge-extra">🟡 {len(extra_list)} Extra</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Overview columns: Vocabulary & Metrics
                info_col1, info_col2 = st.columns([3, 1])
                with info_col1:
                    # 1. Target Words
                    st.markdown(f"**🎯 Target Vocabulary ({len(target_list)}):**")
                    if target_list:
                        pills_html = " ".join(f'<span class="target-pill">{w}</span>' for w in target_list)
                        st.markdown(pills_html, unsafe_allow_html=True)
                    else:
                        st.error("⚠️ Target words are empty! Click '✏️ Edit Song Details, Words & Metadata' below to add them by hand.")

                    # 2. Bonus NGSL Hits
                    if bonus_list:
                        st.markdown(f"<div style='margin-top: 8px;'><b>🔵 Bonus NGSL Hits ({len(bonus_list)}):</b></div>", unsafe_allow_html=True)
                        bonus_html = " ".join(f'<span class="bonus-pill">{w}</span>' for w in bonus_list)
                        st.markdown(bonus_html, unsafe_allow_html=True)

                    # 3. Previously Covered Reused Words
                    if reused_list:
                        st.markdown(f"<div style='margin-top: 8px;'><b>⚪ Previously Covered Words ({len(reused_list)}):</b></div>", unsafe_allow_html=True)
                        reused_html = " ".join(f'<span class="reused-pill">{w}</span>' for w in reused_list)
                        st.markdown(reused_html, unsafe_allow_html=True)

                    # 4. Extra Non-NGSL Words
                    if extra_list:
                        st.markdown(f"<div style='margin-top: 8px;'><b>🟡 Extra Words ({len(extra_list)}):</b></div>", unsafe_allow_html=True)
                        extra_html = " ".join(f'<span class="extra-pill">{w}</span>' for w in extra_list)
                        st.markdown(extra_html, unsafe_allow_html=True)

                with info_col2:
                    st.metric(
                        label="🔥 Total New NGSL",
                        value=f"+{total_new_words} Words",
                        delta=f"🟢 {len(target_list)} Targets + 🔵 {len(bonus_list)} Bonus",
                        delta_color="normal",
                        help="Total brand-new NGSL vocabulary introduced in this song (Targets + New Bonus Hits)"
                    )
                    words_in_lyrics = len(lyrics_text.split())
                    lines_in_lyrics = len([l for l in lyrics_text.splitlines() if l.strip()])
                    st.metric("Song Length", f"{words_in_lyrics} words", help=f"{lines_in_lyrics} lines")

                st.markdown("<hr style='margin: 15px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

                # 💡 Story / Creative Concept
                st.markdown("##### 💡 Story / Creative Concept (Generated by Gemini, fully editable by you):")
                if concept_val:
                    st.markdown(
                        f"""
                        <div style="background: rgba(99, 102, 241, 0.08); border-left: 4px solid #6366F1; padding: 12px 16px; border-radius: 8px; margin-bottom: 12px; font-size: 0.96rem; line-height: 1.6; color: #E2E8F0;">
                            {concept_val}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.info("💡 No story concept recorded yet for this song. You can write one in the edit section below or run Gemini analysis.")

                # 🤖 Step 2: Gemini Flash Mood & Musical Analysis
                st.markdown("##### 🤖 Step 2: Gemini Flash Mood & Musical Analysis:")
                
                # Musical Direction cards (Genre & Structure)
                g_col1, g_col2 = st.columns(2)
                with g_col1:
                    st.markdown(
                        f"""
                        <div style="background: rgba(30, 41, 59, 0.6); padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 10px;">
                            <span style="color: #94A3B8; font-size: 0.85rem;">🎶 Musical Genre</span><br>
                            <strong style="color: #38BDF8; font-size: 1.05rem;">{genre_val or 'Not specified'}</strong>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with g_col2:
                    st.markdown(
                        f"""
                        <div style="background: rgba(30, 41, 59, 0.6); padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08); margin-bottom: 10px;">
                            <span style="color: #94A3B8; font-size: 0.85rem;">🎼 Song Structure</span><br>
                            <strong style="color: #A78BFA; font-size: 1.05rem;">{structure_val or 'Not specified'}</strong>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # Mood Profile Breakdown
                if mood_dict and isinstance(mood_dict, dict):
                    mood_col1, mood_col2 = st.columns([1.5, 2])
                    with mood_col1:
                        st.markdown("**Emotional Mood Breakdown:**")
                        sorted_moods = sorted(
                            mood_dict.items(),
                            key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0,
                            reverse=True
                        )
                        sub_cols = st.columns(min(len(sorted_moods), 3))
                        for m_idx, (m_name, m_pct) in enumerate(sorted_moods[:3]):
                            with sub_cols[m_idx]:
                                st.metric(label=m_name, value=f"{m_pct}%")
                    with mood_col2:
                        mood_df = pd.DataFrame(list(mood_dict.items()), columns=["Mood", "Percentage"])
                        mood_df = mood_df.sort_values(by="Percentage", ascending=False)
                        st.bar_chart(mood_df.set_index("Mood"), color="#4F46E5", height=160)
                else:
                    st.caption("ℹ️ No mood percentage breakdown recorded yet.")

                st.markdown("<hr style='margin: 15px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
                st.markdown(f'<div class="lyrics-box">{lyrics_text}</div>', unsafe_allow_html=True)

                # Action buttons row
                act_c1, act_c2, _ = st.columns([1.5, 2, 2.5])
                with act_c1:
                    clean_filename = "".join(c for c in song_title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
                    st.download_button(
                        label="📥 Download Lyrics",
                        data=lyrics_text,
                        file_name=f"{clean_filename or 'song'}.txt",
                        mime="text/plain",
                        key=f"dl_song_{song_id}"
                    )
                with act_c2:
                    if st.button(
                        "🗑️ Delete Song (Safe Rollback)",
                        key=f"del_song_{song_id}",
                        help=f"Delete '{song_title}' with safety confirmation and automatic dictionary rollback"
                    ):
                        confirm_delete_song_dialog(song_id, song_title, row_num)

                # ──────────────────────────────────────────────────────────────
                # 💿 TRACK VARIANTS & PACKAGING (SUNO + POSTER)
                # ──────────────────────────────────────────────────────────────
                saved_variants = db.get_track_variants(song_id)
                variants_count = len(saved_variants)
                variant_expander_title = f"💿 Track Variants & Packaging ({variants_count})" if variants_count > 0 else "💿 Track Variants & Packaging"

                with st.expander(variant_expander_title, expanded=(variants_count > 0)):
                    st.markdown("##### 💿 Audio & Visual Production Package (Suno AI + Midjourney/DALL-E)")
                    st.caption(
                        "Generate unified style variations (Covers) for this song with a single click: a keyword-optimized music style prompt for Suno AI (< 120 chars, BPM, vocal clarity) paired with an aesthetic album cover prompt for Midjourney / DALL-E featuring artistic typography."
                    )

                    # Controls: Genre, Vocalist, Generate Button
                    p_c1, p_c2, p_c3 = st.columns([2, 1.5, 2])
                    with p_c1:
                        default_p_genre_idx = GENRES.index(genre_val) if genre_val in GENRES else 0
                        p_selected_genre = st.selectbox(
                            "🎨 Visual & Musical Genre",
                            GENRES,
                            index=default_p_genre_idx,
                            key=f"variant_genre_{song_id}"
                        )
                    with p_c2:
                        p_selected_vocalist = st.selectbox(
                            "🎤 Lead Vocalist",
                            ["Male", "Female", "Duet", "Instrumental"],
                            key=f"variant_vocalist_{song_id}"
                        )
                    with p_c3:
                        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                        gen_variant_btn = st.button(
                            "✨ Generate Package (Suno + Poster)",
                            key=f"btn_gen_variant_{song_id}",
                            type="primary",
                            use_container_width=True
                        )

                    if gen_variant_btn:
                        existing = db.get_track_variant_by_combo(song_id, p_selected_genre, p_selected_vocalist)
                        if existing:
                            confirm_overwrite_variant_dialog(
                                song_id=song_id,
                                song_title=song_title,
                                lyrics_text=lyrics_text,
                                genre=p_selected_genre,
                                vocalist=p_selected_vocalist
                            )
                        else:
                            with st.spinner(f"Creating production package for '{song_title}' ({p_selected_genre} • {p_selected_vocalist})..."):
                                res = gemini_client.generate_track_variant(
                                    title=song_title,
                                    lyrics=lyrics_text,
                                    genre=p_selected_genre,
                                    vocalist=p_selected_vocalist
                                )
                                if res.get("success"):
                                    new_suno_p = res.get("suno_prompt", "").strip()
                                    new_poster_p = res.get("poster_prompt", "").strip()
                                    db.upsert_track_variant(
                                        song_id=song_id,
                                        genre=p_selected_genre,
                                        vocalist=p_selected_vocalist,
                                        suno_prompt=new_suno_p,
                                        poster_prompt=new_poster_p
                                    )
                                    st.session_state["lib_toast_msg"] = f"Track package for '{p_selected_genre}' ({p_selected_vocalist}) generated & saved!"
                                    st.rerun()
                                else:
                                    st.error(f"Failed to generate package: {res.get('error')}")

                    # Display saved track variants
                    if saved_variants:
                        st.markdown("<hr style='margin: 15px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
                        st.markdown(f"**Saved Style Packages ({len(saved_variants)}):**")

                        for v_row in saved_variants:
                            v_id = int(v_row["id"])
                            v_genre = v_row["genre"]
                            v_vocalist = v_row["vocalist"]
                            v_suno = v_row["suno_prompt"]
                            v_poster = v_row["poster_prompt"]
                            v_date = v_row["created_at"]

                            st.markdown(
                                f"""
                                <div style="background: rgba(30, 41, 59, 0.55); border: 1px solid rgba(255,255,255,0.12); border-radius: 8px; padding: 10px 14px; margin-top: 14px; margin-bottom: 8px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span>
                                            <span style="background: #3B82F6; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.85rem; font-weight: 700; margin-right: 8px;">🎨 {v_genre}</span>
                                            <span style="background: #8B5CF6; color: white; padding: 3px 10px; border-radius: 6px; font-size: 0.85rem; font-weight: 700;">🎤 {v_vocalist}</span>
                                        </span>
                                        <span style="color: #94A3B8; font-size: 0.82rem;">📅 {v_date}</span>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            # Section 1: Suno Music Prompt
                            st.markdown("##### 🎵 Suno AI Music Style Prompt:")
                            card_edited_suno = st.text_area(
                                label=f"Suno Prompt #{v_id}",
                                value=v_suno,
                                height=75,
                                label_visibility="collapsed",
                                key=f"txt_suno_{v_id}"
                            )
                            suno_char_count = len(card_edited_suno)
                            count_color = "#10B981" if suno_char_count <= 120 else "#EF4444"
                            st.markdown(
                                f"<div style='display: flex; justify-content: space-between; align-items: center; margin-top: -8px; margin-bottom: 6px;'>"
                                f"<small style='color: #94A3B8;'>📋 Click the copy icon in the box below to paste into Suno</small>"
                                f"<small style='color: {count_color}; font-weight: 600;'>Length: {suno_char_count} / 120 chars</small>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                            st.code(card_edited_suno, language="markdown")

                            # Section 2: Poster Image Prompt
                            st.markdown("##### 🎨 Midjourney / DALL-E Album Cover Prompt:")
                            card_edited_poster = st.text_area(
                                label=f"Poster Prompt #{v_id}",
                                value=v_poster,
                                height=110,
                                label_visibility="collapsed",
                                key=f"txt_poster_{v_id}"
                            )
                            st.caption("📋 Click the copy icon in the box below to paste into Midjourney / DALL-E:")
                            st.code(card_edited_poster, language="markdown")

                            # Action buttons: Save Edits, Regenerate, Delete
                            c_btn1, c_btn2, c_btn3 = st.columns([1.5, 1.5, 1.5])
                            with c_btn1:
                                if st.button("💾 Save Edits", key=f"btn_save_var_{v_id}", use_container_width=True):
                                    db.update_track_variant(v_id, card_edited_suno, card_edited_poster)
                                    st.session_state["lib_toast_msg"] = f"Variant package for '{v_genre}' ({v_vocalist}) saved successfully!"
                                    st.rerun()

                            with c_btn2:
                                if st.button("🔄 Regenerate Package", key=f"btn_regen_var_{v_id}", use_container_width=True, help="Re-generate both Suno and Poster prompts with safety confirmation"):
                                    confirm_overwrite_variant_dialog(
                                        song_id=song_id,
                                        song_title=song_title,
                                        lyrics_text=lyrics_text,
                                        genre=v_genre,
                                        vocalist=v_vocalist
                                    )

                            with c_btn3:
                                if st.button("🗑️ Delete", key=f"btn_del_var_{v_id}", use_container_width=True):
                                    confirm_delete_variant_dialog(v_id, v_genre, v_vocalist)

                            st.markdown("<hr style='margin: 16px 0 20px 0; border-color: rgba(255,255,255,0.06);'>", unsafe_allow_html=True)
                    else:
                        st.info("ℹ️ No production packages generated yet for this song. Choose a genre and vocalist above and click **Generate Package (Suno + Poster)**.")

                # In-Place Song & Target Words Editor
                with st.expander("✏️ Edit Song Details, Words & Metadata", expanded=(len(target_list) == 0)):
                    with st.form(key=f"edit_form_{song_id}"):
                        st.markdown(f"#### ✏️ Editing Song #{row_num} — {song_title}")
                        st.caption(f"Database Record ID: #{song_id}")
                        
                        e_col1, e_col2, e_col3 = st.columns([2, 1, 1])
                        with e_col1:
                            new_title = st.text_input("Song Title", value=song_title, key=f"edit_title_{song_id}")
                        with e_col2:
                            default_g_idx = GENRES.index(genre_val) if genre_val in GENRES else 0
                            new_genre = st.selectbox("Genre", GENRES, index=default_g_idx, key=f"edit_genre_{song_id}")
                        with e_col3:
                            default_s_idx = SONG_STRUCTURES.index(structure_val) if structure_val in SONG_STRUCTURES else 0
                            new_structure = st.selectbox("Song Structure", SONG_STRUCTURES, index=default_s_idx, key=f"edit_struct_{song_id}")

                        new_concept = st.text_area(
                            "💡 Story / Creative Concept (Generated by Gemini, fully editable by you):",
                            value=concept_val,
                            height=85,
                            help="Story scenario and narrative concept for this song.",
                            key=f"edit_concept_{song_id}"
                        )

                        new_targets = st.text_area(
                            "🎯 Target Words (comma-separated):",
                            value=target_words_raw,
                            placeholder="e.g. coffee, application, negotiate, salary, employer, client...",
                            help="Primary target vocabulary for this song.",
                            key=f"edit_targets_{song_id}"
                        )

                        e_w_col1, e_w_col2, e_w_col3 = st.columns(3)
                        with e_w_col1:
                            new_bonuses = st.text_area(
                                "🔵 Bonus NGSL Words (comma-separated):",
                                value=bonus_words_raw,
                                placeholder="Incidental new NGSL words found in song...",
                                help="New incidental words from NGSL introduced in this song.",
                                key=f"edit_bonuses_{song_id}"
                            )
                        with e_w_col2:
                            new_reused = st.text_area(
                                "⚪ Previously Covered Words:",
                                value=reused_words_raw,
                                placeholder="NGSL words previously covered...",
                                help="NGSL words already introduced in earlier songs.",
                                key=f"edit_reused_{song_id}"
                            )
                        with e_w_col3:
                            new_extras = st.text_area(
                                "🟡 Extra Words (comma-separated):",
                                value=extra_words_raw,
                                placeholder="Non-NGSL words tracked...",
                                help="Non-NGSL words tracked in extra_words table.",
                                key=f"edit_extras_{song_id}"
                            )

                        new_lyrics = st.text_area(
                            "Song Lyrics:",
                            value=lyrics_text,
                            height=200,
                            key=f"edit_lyrics_{song_id}"
                        )

                        sync_ngsl_chk = st.checkbox(
                            "Sync & increment usage_count in NGSL Dictionary for any new target words added",
                            value=True,
                            key=f"sync_ngsl_{song_id}",
                            help="If checked, any newly added target words will increment the NGSL usage counter."
                        )

                        save_btn = st.form_submit_button("💾 Save Updates", type="primary", use_container_width=True)
                        if save_btn:
                            db.update_song(
                                song_id=song_id,
                                title=new_title.strip() or song_title,
                                lyrics=new_lyrics.strip(),
                                target_words=new_targets.strip(),
                                bonus_words=new_bonuses.strip(),
                                reused_words=new_reused.strip(),
                                extra_words=new_extras.strip(),
                                genre=new_genre,
                                song_structure=new_structure,
                                creative_concept=new_concept.strip(),
                                sync_ngsl_usage=sync_ngsl_chk
                            )
                            updated_title = new_title.strip() or song_title
                            st.session_state["lib_toast_msg"] = f"Song #{row_num} ('{updated_title}') updated successfully!"
                            st.rerun()

                    # Gemini Re-analysis helper button
                    st.markdown("##### 🤖 Re-analyze Mood & Story with Gemini:")
                    if st.button(f"✨ Run Gemini Mood & Story Analysis on Target Words", key=f"gemini_reanalyze_{song_id}"):
                        target_words_to_analyze = [w.strip() for w in target_words_raw.split(",") if w.strip()]
                        if not target_words_to_analyze:
                            st.warning("Please enter and save target words above first before running Gemini analysis.")
                        else:
                            with st.spinner("Analyzing target vocabulary with Gemini..."):
                                res = gemini_client.analyze_vocabulary_mood(target_words_to_analyze)
                                if res.get("success"):
                                    db.update_song(
                                        song_id=song_id,
                                        title=song_title,
                                        lyrics=lyrics_text,
                                        target_words=target_words_raw,
                                        bonus_words=bonus_words_raw,
                                        reused_words=reused_words_raw,
                                        extra_words=extra_words_raw,
                                        mood_breakdown=res.get("mood_breakdown"),
                                        genre=res.get("genre", genre_val),
                                        song_structure=res.get("song_structure", structure_val),
                                        creative_concept=res.get("creative_concept", concept_val),
                                        sync_ngsl_usage=False
                                    )
                                    st.session_state["lib_toast_msg"] = f"Gemini Mood & Story Analysis completed and saved to Song #{row_num}!"
                                    st.rerun()
                                else:
                                    st.error(f"Gemini analysis failed: {res.get('error')}")

