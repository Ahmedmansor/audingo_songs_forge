"""
styles.py — Global CSS and UI theming for Audingo Songs Forge.
"""

import streamlit as st


def apply_custom_styles():
    """Injects all custom styles and typography into the Streamlit app."""
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
    
    [data-testid="stSidebarHeader"] {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    [data-testid="stSidebarContent"] {
        padding-top: 0.4rem !important;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 0 !important;
    }
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0.4rem !important;
        padding-bottom: 0.8rem !important;
    }
    
    .sb-brand-hero {
        background: linear-gradient(135deg, rgba(79, 70, 229, 0.18) 0%, rgba(6, 182, 212, 0.14) 100%);
        border: 1px solid rgba(99, 102, 241, 0.35);
        border-radius: 12px;
        padding: 10px 10px 8px 10px;
        margin-bottom: 8px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
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
        font-size: 1.4rem;
        display: inline-block;
        margin-bottom: 1px;
        filter: drop-shadow(0 2px 8px rgba(99, 102, 241, 0.6));
    }
    .sb-title {
        font-size: 1.12rem;
        font-weight: 800;
        letter-spacing: -0.3px;
        background: linear-gradient(90deg, #C7D2FE, #38BDF8, #A78BFA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2px;
        line-height: 1.2;
    }
    .sb-badge {
        display: inline-block;
        font-size: 0.64rem;
        font-weight: 700;
        letter-spacing: 0.6px;
        text-transform: uppercase;
        padding: 2px 7px;
        border-radius: 20px;
        background: rgba(99, 102, 241, 0.25);
        color: #C7D2FE;
        border: 1px solid rgba(165, 180, 252, 0.35);
        margin-bottom: 4px;
    }
    .sb-subtitle {
        font-size: 0.7rem;
        color: #94A3B8;
        line-height: 1.35;
        margin: 0;
    }
    
    .sb-progress-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 10px;
        padding: 8px 11px;
        margin-bottom: 8px;
        backdrop-filter: blur(8px);
    }
    .sb-progress-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 5px;
    }
    .sb-progress-title {
        font-size: 0.78rem;
        font-weight: 700;
        color: #F1F5F9;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .sb-progress-pct {
        font-size: 0.95rem;
        font-weight: 800;
        color: #34D399;
        font-family: monospace;
    }
    .sb-progress-bar-bg {
        width: 100%;
        height: 6px;
        background: rgba(51, 65, 85, 0.75);
        border-radius: 6px;
        overflow: hidden;
        margin-bottom: 5px;
    }
    .sb-progress-bar-fill {
        height: 100%;
        border-radius: 6px;
        background: linear-gradient(90deg, #6366F1 0%, #06B6D4 50%, #10B981 100%);
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
        transition: width 0.6s ease;
    }
    .sb-progress-caption {
        font-size: 0.68rem;
        color: #94A3B8;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .sb-stat-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 6px;
        margin-bottom: 8px;
    }
    .sb-stat-tile {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 10px;
        padding: 7px 5px;
        text-align: center;
        transition: all 0.22s ease;
        position: relative;
        backdrop-filter: blur(6px);
    }
    .sb-stat-tile:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 14px rgba(0, 0, 0, 0.35);
    }
    .sb-stat-tile-indigo { border: 1px solid rgba(99, 102, 241, 0.3); }
    .sb-stat-tile-indigo:hover {
        border-color: rgba(129, 140, 248, 0.6);
        background: rgba(99, 102, 241, 0.14);
    }
    .sb-stat-tile-green { border: 1px solid rgba(16, 185, 129, 0.3); }
    .sb-stat-tile-green:hover {
        border-color: rgba(52, 211, 153, 0.6);
        background: rgba(16, 185, 129, 0.14);
    }
    .sb-stat-tile-amber { border: 1px solid rgba(245, 158, 11, 0.3); }
    .sb-stat-tile-amber:hover {
        border-color: rgba(251, 191, 36, 0.6);
        background: rgba(245, 158, 11, 0.14);
    }
    .sb-stat-tile-purple { border: 1px solid rgba(168, 85, 247, 0.3); }
    .sb-stat-tile-purple:hover {
        border-color: rgba(192, 132, 252, 0.6);
        background: rgba(168, 85, 247, 0.14);
    }
    .sb-tile-icon { font-size: 0.95rem; margin-bottom: 1px; }
    .sb-tile-val {
        font-size: 1.15rem;
        font-weight: 800;
        letter-spacing: -0.3px;
        line-height: 1.1;
        margin-bottom: 1px;
    }
    .sb-tile-val-indigo { color: #A5B4FC; }
    .sb-tile-val-green { color: #34D399; }
    .sb-tile-val-amber { color: #FBBF24; }
    .sb-tile-val-purple { color: #C084FC; }
    .sb-tile-label {
        font-size: 0.66rem;
        font-weight: 700;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.3px;
        margin-bottom: 1px;
    }
    .sb-tile-sub { font-size: 0.6rem; color: #64748B; }

    .sb-songs-banner {
        background: linear-gradient(135deg, rgba(236, 72, 153, 0.12) 0%, rgba(139, 92, 246, 0.12) 100%);
        border: 1px solid rgba(236, 72, 153, 0.3);
        border-radius: 10px;
        padding: 6px 10px;
        margin-bottom: 7px;
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

    .sb-domain-card {
        background: rgba(30, 41, 59, 0.55);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 10px;
        padding: 8px 10px;
        margin-bottom: 8px;
        backdrop-filter: blur(6px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    .sb-domain-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.15);
        padding-bottom: 4px;
    }
    .sb-domain-title {
        font-size: 0.74rem;
        font-weight: 800;
        color: #F1F5F9;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .sb-domain-total {
        font-size: 0.68rem;
        font-weight: 700;
        color: #FBBF24;
        background: rgba(245, 158, 11, 0.15);
        border: 1px solid rgba(245, 158, 11, 0.3);
        padding: 1px 6px;
        border-radius: 8px;
    }
    .sb-domain-row { margin-bottom: 6px; }
    .sb-domain-row:last-child { margin-bottom: 0; }
    .sb-domain-bar-bg {
        width: 100%;
        height: 4px;
        background: rgba(51, 65, 85, 0.6);
        border-radius: 3px;
        overflow: hidden;
    }
    .sb-domain-bar-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)
