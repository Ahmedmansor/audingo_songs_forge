"""A compact library: one selected song, one detail section at a time."""

from html import escape
import json
import math
import pandas as pd
import streamlit as st
import db
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
    songs["row_num"] = songs["id"].rank(method="dense", ascending=True).astype(int)
    with st.container(key="library_toolbar"):
        a, b = st.columns([2, 1])
        query = a.text_input("Search songs", placeholder="Title, lyrics or vocabulary…", key="library_search", icon=":material/search:")
        order = b.selectbox("Sort by", ["Newest first", "Oldest first", "Title A–Z"], key="library_sort")
    filtered = songs
    if query.strip():
        mask = pd.Series(False, index=songs.index)
        for field in ("title", "lyrics", "target_words", "bonus_words", "reused_words", "extra_words"):
            mask |= songs[field].fillna("").astype(str).str.contains(query.strip(), case=False, regex=False)
        filtered = songs[mask]
    if order == "Oldest first":
        filtered = filtered.sort_values("id")
    elif order == "Title A–Z":
        filtered = filtered.sort_values("title", key=lambda col: col.str.lower())
    st.caption(f"{len(filtered)} of {len(songs)} songs")
    if filtered.empty:
        st.info("No songs match this search. Try another word.")
        return
    records = {int(row["id"]): row for _, row in filtered.iterrows()}
    selected = st.selectbox("Open a song", options=list(records),
        format_func=lambda song_id: f"#{records[song_id]['row_num']} · {records[song_id]['title']}", key="library_selected_song")
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
