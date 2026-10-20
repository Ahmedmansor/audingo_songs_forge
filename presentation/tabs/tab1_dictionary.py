"""
tab1_dictionary.py — Tab 1: Dictionary & Analytics.
"""

import streamlit as st
from constants import DOMAINS, DOMAIN_CONFIG
import db
from presentation.components.identity import domain_card, icon_svg


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

    # Live Remaining Words Breakdown Table by POS (Audingo Apple-surface design)
    render_remaining_pos_table()

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


def render_remaining_pos_table():
    """Renders a clean, live breakdown table of remaining unused words by Domain and POS matching Audingo design system."""
    stats_data = db.get_domain_pos_remaining_stats()
    if not stats_data:
        return

    tot_nouns = sum(r["nouns"] for r in stats_data)
    tot_verbs = sum(r["verbs"] for r in stats_data)
    tot_adjs = sum(r["adjectives"] for r in stats_data)
    tot_advs = sum(r["adverbs"] for r in stats_data)
    tot_exempt = sum(r["exempt"] for r in stats_data)
    tot_all = sum(r["total"] for r in stats_data)

    def _val(num: int) -> str:
        if num == 0:
            return '<span style="color: var(--studio-muted); opacity: 0.35;">—</span>'
        return f'<span style="color: var(--studio-ink); font-weight: 600;">{num:,}</span>'

    rows_html = []
    for r in stats_data:
        dom = r["domain"]

        row = f"""
        <tr style="border-bottom: 1px solid var(--studio-line); transition: background-color 140ms ease;">
            <td style="padding: 12px 14px; text-align: left; vertical-align: middle; white-space: nowrap;">
                <div style="display: inline-flex; align-items: center; gap: 10px;">
                    <span class="icon-tile" style="width: 32px; height: 32px; border-radius: 9px; flex-shrink: 0;">
                        {icon_svg(dom)}
                    </span>
                    <strong style="color: var(--studio-ink); font-size: 0.88rem; letter-spacing: -0.01em;">{dom}</strong>
                </div>
            </td>
            <td style="padding: 12px 14px; text-align: center; vertical-align: middle;">{_val(r['nouns'])}</td>
            <td style="padding: 12px 14px; text-align: center; vertical-align: middle;">{_val(r['verbs'])}</td>
            <td style="padding: 12px 14px; text-align: center; vertical-align: middle;">{_val(r['adjectives'])}</td>
            <td style="padding: 12px 14px; text-align: center; vertical-align: middle;">{_val(r['adverbs'])}</td>
            <td style="padding: 12px 14px; text-align: center; vertical-align: middle;">{_val(r['exempt'])}</td>
            <td style="padding: 12px 14px; text-align: center; vertical-align: middle;">
                <span class="domain-song-pill" style="font-size: 0.8rem; font-weight: 600; padding: 3px 10px;">
                    {r['total']:,} left
                </span>
            </td>
        </tr>
        """
        rows_html.append(row)

    total_row = f"""
    <tr style="background: var(--studio-neutral-bg); border-top: 2px solid var(--studio-line); font-weight: 650;">
        <td style="padding: 14px 14px; text-align: left; vertical-align: middle; color: var(--studio-ink);">
            <div style="display: inline-flex; align-items: center; gap: 8px;">
                <span class="icon-tile" style="width: 32px; height: 32px; border-radius: 9px; flex-shrink: 0; background: var(--studio-tint);">
                    {icon_svg("wave")}
                </span>
                <span style="font-size: 0.92rem; font-weight: 650; letter-spacing: -0.015em;">Total Remaining Words</span>
            </div>
        </td>
        <td style="padding: 14px 14px; text-align: center; vertical-align: middle; font-size: 0.95rem;">{_val(tot_nouns)}</td>
        <td style="padding: 14px 14px; text-align: center; vertical-align: middle; font-size: 0.95rem;">{_val(tot_verbs)}</td>
        <td style="padding: 14px 14px; text-align: center; vertical-align: middle; font-size: 0.95rem;">{_val(tot_adjs)}</td>
        <td style="padding: 14px 14px; text-align: center; vertical-align: middle; font-size: 0.95rem;">{_val(tot_advs)}</td>
        <td style="padding: 14px 14px; text-align: center; vertical-align: middle; font-size: 0.95rem;">{_val(tot_exempt)}</td>
        <td style="padding: 14px 14px; text-align: center; vertical-align: middle;">
            <span class="domain-song-pill active" style="font-size: 0.88rem; padding: 4px 14px; font-weight: 700;">
                {tot_all:,} total left
            </span>
        </td>
    </tr>
    """

    card_html = f"""
    <article class="domain-card" style="margin: 22px 0 28px; padding: 22px 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 12px;">
            <div>
                <div class="studio-eyebrow" style="margin-bottom: 4px;">Vocabulary Balance & Remaining Reserve</div>
                <h3 style="margin: 0; font-size: 1.15rem; font-weight: 650; letter-spacing: -0.02em; color: var(--studio-ink);">
                    Remaining Unused Words by Part of Speech
                </h3>
                <p style="margin: 3px 0 0; font-size: 0.82rem; color: var(--studio-muted);">
                    Live inventory of all {tot_all:,} remaining NGSL words categorized across domains and grammatical types
                </p>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span class="domain-song-pill active" style="font-size: 0.84rem; padding: 5px 14px;">
                    {tot_all:,} words to 100% mastery
                </span>
            </div>
        </div>
        <div style="overflow-x: auto; border-radius: 14px; border: 1px solid var(--studio-line);">
            <table style="width: 100%; border-collapse: collapse; font-size: 0.86rem; font-variant-numeric: tabular-nums;">
                <thead>
                    <tr style="border-bottom: 1px solid var(--studio-line); background: var(--studio-bg); color: var(--studio-muted);">
                        <th style="padding: 11px 14px; text-align: left; font-weight: 600; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.05em;">Domain</th>
                        <th style="padding: 11px 14px; text-align: center; font-weight: 600;"><span class="badge-noun">Nouns</span></th>
                        <th style="padding: 11px 14px; text-align: center; font-weight: 600;"><span class="badge-verb">Verbs</span></th>
                        <th style="padding: 11px 14px; text-align: center; font-weight: 600;"><span class="badge-adj">Adjectives</span></th>
                        <th style="padding: 11px 14px; text-align: center; font-weight: 600;"><span class="stat-badge" style="background: rgba(115, 82, 162, 0.12); color: var(--studio-purple); border: 1px solid rgba(115, 82, 162, 0.25);">Adverbs</span></th>
                        <th style="padding: 11px 14px; text-align: center; font-weight: 600;"><span class="stat-badge" style="background: var(--studio-neutral-bg); color: var(--studio-neutral-ink); border: 1px solid var(--studio-line);">Exempt</span></th>
                        <th style="padding: 11px 14px; text-align: center; font-weight: 600; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--studio-blue);">Remaining</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows_html)}
                </tbody>
                <tfoot>
                    {total_row}
                </tfoot>
            </table>
        </div>
    </article>
    """
    st.html(card_html)


