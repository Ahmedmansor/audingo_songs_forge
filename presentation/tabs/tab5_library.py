"""A compact library: one selected song, one detail section at a time."""

from html import escape
import json
import math
import pandas as pd
import streamlit as st
import db
from constants import DOMAINS, DOMAIN_CONFIG
from presentation.components.identity import icon_svg
from presentation.components.widgets import format_cairo_display_time, render_domain_breakdown_section
from presentation.components.refinement_report import render_saved_refinement_report
from presentation.components.library_sections import render_library_editor, render_library_production
from domain.services.refinement_archive import parse_refinement_snapshot, report_matches_lyrics

SECTIONS = {
    "Overview": ":material/space_dashboard: Overview",
    "Vocabulary": ":material/menu_book: Vocabulary",
    "Critic": ":material/fact_check: Critic",
    "Production": ":material/graphic_eq: Production",
    "Edit": ":material/edit_note: Edit",
}


def _words(value):
    return [word.strip() for word in (value or "").split(",") if word.strip()]


def _render_library_category_distribution(songs: pd.DataFrame):
    """Render stacked percentage distribution and badges for all song categories in the library."""
    if songs.empty:
        return
    total_songs = len(songs)
    cat_series = songs["source_domain"].fillna("").replace("", "Not tagged")
    cat_counts = cat_series.value_counts()

    ordered_cats = [d for d in DOMAINS if d in cat_counts]
    for c in cat_counts.index:
        if c not in ordered_cats and c != "Not tagged":
            ordered_cats.append(c)
    if "Not tagged" in cat_counts and "Not tagged" not in ordered_cats:
        ordered_cats.append("Not tagged")

    bar_segments = []
    badges = []

    for cat in ordered_cats:
        cnt = int(cat_counts.get(cat, 0))
        if cnt == 0:
            continue
        pct = (cnt / total_songs) * 100.0
        cfg = DOMAIN_CONFIG.get(cat, {
            "emoji": "🏷️",
            "color": "var(--studio-muted)",
            "bg": "rgba(148, 163, 184, 0.12)",
            "border": "rgba(148, 163, 184, 0.3)",
        })
        emoji = cfg.get("emoji", "🏷️")
        color = cfg.get("color", "var(--studio-muted)")
        bg = cfg.get("bg", "rgba(148, 163, 184, 0.12)")
        border = cfg.get("border", "rgba(148, 163, 184, 0.3)")
        song_lbl = "song" if cnt == 1 else "songs"

        title_attr = escape(f"{emoji} {cat}: {pct:.1f}% ({cnt} {song_lbl})", quote=True)
        bar_segments.append(
            f'<div style="width: {pct:.2f}%; height: 100%; background: {color};" title="{title_attr}"></div>'
        )
        badges.append(
            f'<span style="background: {bg}; color: {color}; border: 1px solid {border}; '
            f'padding: 3px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 700; '
            f'display: inline-flex; align-items: center; gap: 4px;">'
            f'{emoji} {escape(cat)}: <b>{pct:.1f}%</b> <small style="opacity: 0.8;">({cnt})</small>'
            f'</span>'
        )

    bar_html = "".join(bar_segments)
    badges_html = " ".join(badges)
    total_lbl = "song" if total_songs == 1 else "songs"

    box_html = (
        f'<div style="background: var(--studio-bg); border: 1px solid rgba(148, 163, 184, 0.18); '
        f'border-radius: 12px; padding: 10px 14px; margin: 8px 0 14px 0;">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 7px; flex-wrap: wrap; gap: 6px;">'
        f'<span style="font-size: 0.84rem; font-weight: 700; color: var(--studio-ink); display: inline-flex; align-items: center; gap: 6px;">'
        f'📊 <b>Library Category Distribution</b>'
        f'</span>'
        f'<span style="font-size: 0.78rem; font-weight: 600; color: var(--studio-muted);">'
        f'{total_songs} {total_lbl} total'
        f'</span>'
        f'</div>'
        f'<div style="width: 100%; height: 8px; border-radius: 6px; overflow: hidden; display: flex; background: var(--studio-track); margin-bottom: 8px;">'
        f'{bar_html}'
        f'</div>'
        f'<div style="display: flex; flex-wrap: wrap; gap: 6px; align-items: center;">'
        f'{badges_html}'
        f'</div>'
        f'</div>'
    )
    st.markdown(box_html, unsafe_allow_html=True)


def _authenticity_stat(row):
    snapshot = parse_refinement_snapshot(row.get("refinement_report"))
    if snapshot is None:
        return "—", "Authenticity · not recorded"
    try:
        score = float(snapshot["report"].get("overall_score"))
    except (TypeError, ValueError):
        score = float("nan")
    if not math.isfinite(score) or not 0 <= score <= 100:
        return "—", "Authenticity · not recorded"
    label = "Authenticity score" if report_matches_lyrics(snapshot, row["lyrics"] or "") else "Authenticity · archived"
    return f"{score:g}%", label


def _render_overview(row):
    song_id = int(row["id"])
    lyrics = row["lyrics"] or ""
    with st.container(border=True):
        st.markdown(":material/category: **Song category**")
        st.write(row.get("source_domain") or "Not tagged")
    all_ngsl = set().union(*(_words(row.get(field)) for field in ("target_words", "bonus_words", "reused_words")))
    render_domain_breakdown_section(db.compute_domain_breakdown(sorted(all_ngsl)), title="Domain breakdown", compact=True)
    snapshot = parse_refinement_snapshot(row.get("refinement_report"))
    if snapshot and not report_matches_lyrics(snapshot, lyrics):
        st.caption("Authenticity refers to the archived lyrics. Open Critic to review the evaluated version.")
    left, right = st.columns([1.5, 1])
    with left:
        with st.container(border=True):
            st.markdown(":material/lightbulb: **The story**")
            st.write(row.get("creative_concept") or "No story concept recorded yet.")
    with right:
        with st.container(border=True):
            st.markdown(":material/tune: **Musical direction**")
            st.write(row.get("genre") or "Genre not recorded")
            st.caption(row.get("song_structure") or "Structure not recorded")
    mood = row.get("mood_breakdown")
    if isinstance(mood, str):
        try:
            mood = json.loads(mood)
        except (ValueError, TypeError):
            mood = None
    if isinstance(mood, dict):
        values = {key: val for key, val in mood.items() if isinstance(val, (float, int))}
        if values:
            with st.expander(":material/auto_awesome: Mood & musical analysis", expanded=False):
                frame = pd.DataFrame(values.items(), columns=["Mood", "Percentage"]).sort_values("Percentage", ascending=False)
                st.bar_chart(frame.set_index("Mood"), horizontal=True, height=220)
    line_count = sum(bool(line.strip()) for line in lyrics.splitlines())
    with st.expander(f":material/lyrics: Lyrics · {line_count} lines", expanded=False):
        with st.container(height=360):
            st.html(f'<div class="library-lyrics">{escape(lyrics)}</div>')
    name = "".join(c for c in row["title"] if c.isalnum() or c in " _-").strip().replace(" ", "_")
    st.download_button("Download lyrics", data=lyrics, file_name=f"{name or 'song'}.txt", mime="text/plain", icon=":material/download:", key=f"dl_song_{song_id}")


def _render_vocabulary(row):
    groups = [
        ("Target vocabulary", "target_words", "target-pill"),
        ("New bonus NGSL", "bonus_words", "bonus-pill"),
        ("Previously covered NGSL", "reused_words", "reused-pill"),
        ("Extra words", "extra_words", "extra-pill"),
    ]
    for label, field, pill in groups:
        words = _words(row.get(field))
        with st.expander(f":material/menu_book: {label} · {len(words)} words", expanded=False):
            if words:
                st.html('<div class="library-word-list">' + " ".join(f'<span class="{pill}">{escape(word)}</span>' for word in words) + '</div>')
            else:
                st.caption("No words recorded in this group.")


def render_tab_library():
    if "lib_toast_msg" in st.session_state:
        st.toast(st.session_state.pop("lib_toast_msg"), icon=":material/check_circle:")
    st.subheader("Your songs. All together.")
    st.caption("Choose a song. Explore the details when you need them.")
    songs = db.get_all_songs()
    if songs.empty:
        with st.container(border=True):
            st.markdown(":material/library_music: **Your library starts here.**")
            st.caption("Approve your first song in Commit Lab to save its lyrics, vocabulary, critic report and production packages.")
        return
    songs = songs.reset_index(drop=True)
    if "source_domain" not in songs:
        songs["source_domain"] = None
    category_labels = songs["source_domain"].fillna("").replace("", "Not tagged")
    songs["row_num"] = songs["id"].rank(method="dense", ascending=True).astype(int)
    _render_library_category_distribution(songs)
    with st.container(key="library_toolbar"):
        a, b = st.columns([2, 1])
        query = a.text_input("Search songs", placeholder="Title, lyrics or vocabulary…", key="library_search", icon=":material/search:")
        order = b.selectbox("Sort by", ["Newest first", "Oldest first", "Title A–Z"], key="library_sort")
        category = st.selectbox("Song category", ["All categories"] + sorted(category_labels.unique()), key="library_category_filter",
            help="The category selected in Studio, independent of the vocabulary breakdown.")
    filtered = songs
    if query.strip():
        mask = pd.Series(False, index=songs.index)
        for field in ("title", "lyrics", "target_words", "bonus_words", "reused_words", "extra_words"):
            mask |= songs[field].fillna("").astype(str).str.contains(query.strip(), case=False, regex=False)
        filtered = songs[mask]
    if category != "All categories":
        filtered = filtered[category_labels.loc[filtered.index] == category]
    if order == "Oldest first":
        filtered = filtered.sort_values("id")
    elif order == "Title A–Z":
        filtered = filtered.sort_values("title", key=lambda col: col.str.lower())
    st.caption(f"{len(filtered)} of {len(songs)} songs")
    if filtered.empty:
        st.info("No songs match this search. Try another word.")
        return
    records = {int(row["id"]): row for _, row in filtered.iterrows()}

    def _format_song_option(song_id: int) -> str:
        r = records[song_id]
        total_new = len(_words(r.get("target_words"))) + len(_words(r.get("bonus_words")))
        words_label = "word" if total_new == 1 else "words"
        words_txt = f"+{total_new} {words_label}" if total_new > 0 else "0 words"
        dom = r.get("source_domain") or "Not tagged"
        cfg = DOMAIN_CONFIG.get(dom, {})
        emoji = cfg.get("emoji", "🏷️") if dom != "Not tagged" else "🏷️"
        return f"#{r['row_num']} • {r['title']}  ·  {words_txt}  ·  {emoji} {dom}"

    selected = st.selectbox(
        "Open a song",
        options=list(records),
        format_func=_format_song_option,
        key="library_selected_song",
    )
    row = records[selected]
    counts = [len(_words(row.get(field))) for field in ("target_words", "bonus_words", "reused_words", "extra_words")]
    date = format_cairo_display_time(row["created_at"])
    score, score_label = _authenticity_stat(row)
    metrics = [(counts[0] + counts[1], "Total new words"), (score, score_label)]
    metrics.extend(zip(counts, ("Target words", "New bonus", "Reused", "Extra words")))
    tones = ("total", "authenticity", "target", "bonus", "reused", "extra")
    stats = ''.join(f'<div class="library-stat-{tone}"><b>{escape(str(value))}</b><span>{label}</span></div>' for tone, (value, label) in zip(tones, metrics))
    st.html(f'''<article class="library-song-card">
<div class="library-song-heading"><span class="library-song-mark">{icon_svg()}</span><div>
<div class="studio-eyebrow">SONG {int(row['row_num']):02d} / AUDINGO</div>
<h3>{escape(row['title'])}</h3><p>{escape(row.get('genre') or 'Your original song')} · {escape(str(date))} · Cairo</p>
</div></div><div class="library-song-stats">{stats}</div></article>''')
    section = st.segmented_control("Song details", list(SECTIONS), default="Overview", required=True,
        format_func=SECTIONS.get, key=f"library_section_{selected}", width="stretch", wrap=True, label_visibility="collapsed")
    with st.container(key="library_detail"):
        if section == "Overview":
            _render_overview(row)
        elif section == "Vocabulary":
            _render_vocabulary(row)
        elif section == "Critic":
            render_saved_refinement_report(row.get("refinement_report"), row["lyrics"] or "", selected)
        elif section == "Production":
            render_library_production(row)
        elif section == "Edit":
            render_library_editor(row)
