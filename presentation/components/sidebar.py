"""
sidebar.py — Sidebar layout, mastery progress bar, and domain breakdown.
"""

import os
import streamlit as st
import db
from constants import DOMAINS, DOMAIN_CONFIG


def render_sidebar():
    """Renders the comprehensive, modern sidebar with mastery metrics and domain stats."""
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

        # 3.5. Domain Remaining Breakdown Widget
        sb_dom_stats = db.get_domain_detailed_stats()
        sb_total_unused = sum(d["unused"] for d in sb_dom_stats.values())

        domain_rows_html = []
        for d_name in DOMAINS:
            cfg = DOMAIN_CONFIG.get(d_name, {})
            d_data = sb_dom_stats.get(d_name, {"total": 0, "used": 0, "unused": 0, "percent_used": 0.0})
            d_tot = d_data["total"]
            d_usd = d_data["used"]
            d_uns = d_data["unused"]
            pct_usd = d_data["percent_used"]
            pct_uns = (d_uns / d_tot * 100) if d_tot > 0 else 0.0
            color = cfg.get("color", "#38BDF8")
            bg = cfg.get("bg", "rgba(56,189,248,0.15)")
            border = cfg.get("border", "rgba(56,189,248,0.3)")
            emoji = cfg.get("emoji", "🎯")

            row_html = (
                f'<div class="sb-domain-row">'
                f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">'
                f'<span style="font-weight: 700; font-size: 0.76rem; color: #F1F5F9; display: flex; align-items: center; gap: 5px;">'
                f'<span>{emoji}</span> <span>{d_name}</span>'
                f'</span>'
                f'<span style="font-size: 0.69rem; font-weight: 800; color: {color}; background: {bg}; border: 1px solid {border}; padding: 1px 6px; border-radius: 6px;">'
                f'{pct_uns:.0f}% Left'
                f'</span>'
                f'</div>'
                f'<div class="sb-domain-bar-bg" style="margin-bottom: 3px;">'
                f'<div class="sb-domain-bar-fill" style="width: {min(pct_usd, 100):.1f}%; background: {color};" title="{d_name}: {d_usd:,} used ({pct_usd:.1f}%), {d_uns:,} remaining ({pct_uns:.1f}%)"></div>'
                f'</div>'
                f'<div style="display: flex; justify-content: space-between; font-size: 0.68rem; color: #94A3B8; font-family: monospace;">'
                f'<span><b style="color: #34D399;">{d_uns:,}</b> <span style="color: #64748B;">/ {d_tot:,}</span></span>'
                f'<span style="color: #64748B;">{d_usd:,} used <small>({pct_usd:.1f}%)</small></span>'
                f'</div>'
                f'</div>'
            )
            domain_rows_html.append(row_html)

        sb_domain_card_html = (
            f'<div class="sb-domain-card">'
            f'<div class="sb-domain-header">'
            f'<span class="sb-domain-title">💎 Unused by Domain</span>'
            f'<span class="sb-domain-total">{sb_total_unused:,} Pool</span>'
            f'</div>'
            f'{"".join(domain_rows_html)}'
            f'</div>'
        )
        st.markdown(sb_domain_card_html, unsafe_allow_html=True)

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
