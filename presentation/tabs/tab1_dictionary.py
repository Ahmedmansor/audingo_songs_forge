"""
tab1_dictionary.py — Tab 1: Dictionary & Analytics.
"""

import streamlit as st
from constants import DOMAINS, DOMAIN_CONFIG
import db


def render_tab_dictionary():
    """Renders the Vocabulary Coverage, Domain Breakdown Cards, and Dictionary Tables."""
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

    # 6-Domain Corpus Breakdown Cards
    domain_stats = db.get_domain_detailed_stats()
    dom_total_corpus = sum(d["total"] for d in domain_stats.values()) or 1
    d_cols = st.columns(len(DOMAINS))
    for idx, d_name in enumerate(DOMAINS):
        cfg = DOMAIN_CONFIG.get(d_name, {})
        data = domain_stats.get(d_name, {"total": 0, "used": 0, "unused": 0, "percent_used": 0.0})
        d_tot = data["total"]
        d_usd = data["used"]
        d_uns = data["unused"]
        pct_used = data["percent_used"]
        corpus_share = (d_tot / dom_total_corpus * 100)
        if idx < len(d_cols):
            with d_cols[idx]:
                card_html = (
                    f'<div style="background: rgba(30, 41, 59, 0.7); border: 1px solid {cfg.get("border", "rgba(148,163,184,0.3)")}; '
                    f'border-radius: 12px; padding: 12px 8px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.18); min-height: 220px; display: flex; flex-direction: column; justify-content: space-between;">'
                    f'<div>'
                    f'<div style="font-size: 1.35rem; margin-bottom: 3px;">{cfg.get("emoji", "")}</div>'
                    f'<div style="font-size: 0.76rem; font-weight: 800; color: #F8FAFC; text-transform: uppercase; letter-spacing: 0.3px; margin-bottom: 8px; min-height: 2.2em; display: flex; align-items: center; justify-content: center;">{d_name}</div>'
                    f'</div>'
                    f'<div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(52, 211, 153, 0.3); border-radius: 8px; padding: 6px 4px; margin-bottom: 8px;">'
                    f'<div style="font-size: 1.3rem; font-weight: 800; color: #34D399; font-family: monospace; line-height: 1.1;">{d_uns:,}</div>'
                    f'<div style="font-size: 0.68rem; font-weight: 700; color: #A7F3D0; text-transform: uppercase; letter-spacing: 0.4px; margin-top: 2px;">Remaining</div>'
                    f'</div>'
                    f'<div>'
                    f'<div style="width: 100%; height: 5px; background: rgba(51, 65, 85, 0.75); border-radius: 4px; overflow: hidden; margin-bottom: 5px;">'
                    f'<div style="width: {pct_used:.1f}%; height: 100%; background: {cfg.get("color", "#38BDF8")};"></div>'
                    f'</div>'
                    f'<div style="font-size: 0.69rem; color: #94A3B8; margin-bottom: 8px;">{pct_used:.1f}% Mastered</div>'
                    f'<div style="display: flex; justify-content: space-between; font-size: 0.70rem; color: #94A3B8; border-top: 1px solid rgba(148,163,184,0.15); padding-top: 6px;">'
                    f'<span>Tot: <b style="color: #F1F5F9;">{d_tot:,}</b> <small>({corpus_share:.0f}%)</small></span>'
                    f'<span>Used: <b style="color: {cfg.get("color", "#38BDF8")};">{d_usd:,}</b></span>'
                    f'</div>'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("---")
    
    # Tables (Symmetrically aligned layout)
    col_ngsl, col_extra = st.columns([1.35, 1])
    
    with col_ngsl:
        st.markdown("#### 📖 NGSL Dictionary")
        ngsl_df = db.get_all_ngsl_words()
        
        if not ngsl_df.empty:
            ngsl_df["Status"] = ngsl_df["usage_count"].apply(lambda c: "✅ Used" if c > 0 else "⏳ Unused")
            
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1:
                pos_filter = st.selectbox("Filter POS", ["All", "Noun", "Verb", "Adjective", "Other"], key="filter_pos")
            with f_col2:
                status_filter = st.selectbox("Filter Status", ["All", "Used", "Unused"], key="filter_status")
            with f_col3:
                domain_filter = st.selectbox("Filter Domain", ["All"] + DOMAINS, key="filter_domain")
            with f_col4:
                search_word = st.text_input("Search Word", placeholder="Type word...", key="filter_search_ngsl")

            filtered_df = ngsl_df.copy()
            if pos_filter != "All":
                filtered_df = filtered_df[filtered_df["pos_type"] == pos_filter]
            if status_filter == "Used":
                filtered_df = filtered_df[filtered_df["usage_count"] > 0]
            elif status_filter == "Unused":
                filtered_df = filtered_df[filtered_df["usage_count"] == 0]
            if domain_filter != "All":
                filtered_df = filtered_df[filtered_df["domain"] == domain_filter]
            if search_word:
                filtered_df = filtered_df[filtered_df["word"].str.contains(search_word.strip().lower(), case=False, na=False)]

            st.dataframe(
                filtered_df[["word", "domain", "coca_top_pct", "pos_type", "Status", "usage_count", "lemma_family"]],
                column_config={
                    "word": "Headword",
                    "domain": "COCA Domain",
                    "coca_top_pct": st.column_config.NumberColumn("Dominance %", format="%.1f%%"),
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
        st.markdown("#### 🌟 Extra Words (Non-NGSL In Songs)")
        extra_df = db.get_extra_words()
        
        ef_col1, ef_col2 = st.columns([1.3, 1])
        with ef_col1:
            search_extra = st.text_input("Search Extra Word", placeholder="Type word...", key="filter_search_extra")
        with ef_col2:
            sort_extra = st.selectbox("Sort By", ["Most Frequent", "A-Z", "First Seen Song"], key="filter_sort_extra")

        if not extra_df.empty:
            filtered_extra = extra_df.copy()
            if search_extra:
                filtered_extra = filtered_extra[filtered_extra["word"].str.contains(search_extra.strip().lower(), case=False, na=False)]
            if sort_extra == "Most Frequent":
                filtered_extra = filtered_extra.sort_values(by="occurrence_count", ascending=False)
            elif sort_extra == "A-Z":
                filtered_extra = filtered_extra.sort_values(by="word", ascending=True)
            elif sort_extra == "First Seen Song":
                filtered_extra = filtered_extra.sort_values(by="first_seen_in_song", ascending=True)

            st.dataframe(
                filtered_extra[["word", "occurrence_count", "first_seen_in_song"]],
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
