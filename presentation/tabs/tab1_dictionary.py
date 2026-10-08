"""
tab1_dictionary.py — Tab 1: Dictionary & Analytics.
"""

import streamlit as st
from constants import DOMAINS, DOMAIN_CONFIG
import db
from presentation.components.identity import domain_card


def render_tab_dictionary():
    """Renders the Vocabulary Coverage, Domain Breakdown Cards, and Dictionary Tables."""
    st.subheader("Your vocabulary, at a glance.")
    st.caption("Track your progress and find the words for your next song.")
    
    stats = db.get_progress_stats()
    with st.container(key="vocabulary_metrics"):
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        with col_stat1:
            st.metric("NGSL vocabulary", f"{stats['total']:,}")
        with col_stat2:
            st.metric("Words mastered", f"{stats['used']:,}", delta=f"{stats['percent']}%")
        with col_stat3:
            st.metric("Ready to explore", f"{stats['unused']:,}")
        with col_stat4:
            st.metric("Extra discoveries", f"{stats['extra_count']:,}")

    # Progress bar
    fraction = (stats['used'] / stats['total']) if stats['total'] > 0 else 0.0
    st.progress(fraction, text=f"Coverage Progress: {stats['used']} / {stats['total']} words ({stats['percent']}%)")

    # Responsive domain summaries share the same outline icon family.
    domain_stats = db.get_domain_detailed_stats()
    st.html('<div class="domain-grid">' + ''.join(
        domain_card(name, domain_stats.get(name, {})) for name in DOMAINS
    ) + '</div>')

    st.markdown("---")
    
    # Tables (Symmetrically aligned layout)
    col_ngsl, col_extra = st.columns([1.35, 1])
    
    with col_ngsl:
        st.markdown("#### :material/menu_book: NGSL Dictionary")
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
                width="stretch",
                height=480
            )
        else:
            st.info("Database is empty. Please run `python build_db.py` to ingest the vocabulary.")

    with col_extra:
        st.markdown("#### :material/stars: Extra Words (Non-NGSL In Songs)")
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
                width="stretch",
                height=480
            )
        else:
            st.info("No extra words tracked yet. They will automatically appear when songs are approved in Commit Lab.")
