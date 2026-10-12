"""A compact library: one selected song, one detail section at a time."""

from html import escape
import json
import math
import re
import pandas as pd
import streamlit as st
import db
from constants import DOMAINS, DOMAIN_CONFIG
from presentation.components.identity import icon_svg
from presentation.components.widgets import (
    format_cairo_display_time,
    render_domain_breakdown_section,
    render_floating_library_song_fab,
    render_library_lyrics_copy_toolbar,
    render_simple_copy_button,
)
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

LYRICS_TAG_REGEX = re.compile(r"(\[[^\]\n]+\])")


def format_lyrics_with_tags(raw_lyrics: str) -> str:
    """Format lyrics by escaping HTML and highlighting bracketed structure tags."""
    if not raw_lyrics:
        return ""
    escaped = escape(raw_lyrics)
    return LYRICS_TAG_REGEX.sub(r'<span class="lyrics-tag">\1</span>', escaped)


def _words(value):
    return [word.strip() for word in (value or "").split(",") if word.strip()]


def _render_library_category_distribution(songs: pd.DataFrame):
    """Render circular donut distribution and badges for all song categories in the library."""
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

    active_cats = [c for c in ordered_cats if int(cat_counts.get(c, 0)) > 0]
    if not active_cats:
        return

    conic_stops = []
    badges = []
    current_deg = 0.0

    for idx, cat in enumerate(active_cats):
        cnt = int(cat_counts.get(cat, 0))
        pct = (cnt / total_songs) * 100.0
        deg = (cnt / total_songs) * 360.0
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

        next_deg = current_deg + deg
        if idx == len(active_cats) - 1:
            next_deg = 360.0

        conic_stops.append(f"{color} {current_deg:.2f}deg {next_deg:.2f}deg")
        current_deg = next_deg

        title_attr = escape(f"{emoji} {cat}: {pct:.1f}% ({cnt} {song_lbl})", quote=True)
        badges.append(
            f'<div style="background: {bg}; border: 1px solid {border}; '
            f'padding: 7px 12px; border-radius: 10px; font-size: 0.81rem; '
            f'display: flex; align-items: center; justify-content: space-between; gap: 8px;" title="{title_attr}">'
            f'<span style="display: inline-flex; align-items: center; gap: 6px; font-weight: 650; color: {color};">'
            f'<span style="width: 8px; height: 8px; border-radius: 50%; background: {color}; display: inline-block; flex-shrink: 0;"></span>'
            f'{emoji} {escape(cat)}'
            f'</span>'
            f'<span style="font-weight: 800; color: {color}; white-space: nowrap;">'
            f'{pct:.1f}% <small style="font-weight: 600; opacity: 0.85;">({cnt})</small>'
            f'</span>'
            f'</div>'
        )

    conic_css = ", ".join(conic_stops)
    badges_html = "".join(badges)
    total_lbl = "song" if total_songs == 1 else "songs"

    box_html = (
        f'<div style="background: var(--studio-surface); border: 1px solid rgba(148, 163, 184, 0.2); '
        f'border-radius: 16px; padding: 14px 18px; margin: 8px 0 16px 0; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);">'
        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 6px; border-bottom: 1px solid rgba(148, 163, 184, 0.12); padding-bottom: 8px;">'
        f'<span style="font-size: 0.86rem; font-weight: 700; color: var(--studio-ink); display: inline-flex; align-items: center; gap: 6px;">'
        f'📊 <b>Library Category Distribution</b>'
        f'</span>'
        f'<span style="font-size: 0.78rem; font-weight: 600; color: var(--studio-muted);">'
        f'{total_songs} {total_lbl} total'
        f'</span>'
        f'</div>'
        f'<div style="display: flex; align-items: center; gap: 22px; flex-wrap: wrap;">'
        f'<div style="display: flex; align-items: center; justify-content: center; flex-shrink: 0; padding: 4px;">'
        f'<div style="width: 124px; height: 124px; border-radius: 50%; background: conic-gradient({conic_css}); '
        f'display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);">'
        f'<div style="width: 82px; height: 82px; border-radius: 50%; background: var(--studio-surface); '
        f'display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; '
        f'box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.04);">'
        f'<span style="font-size: 1.35rem; font-weight: 800; color: var(--studio-ink); line-height: 1;">{total_songs}</span>'
        f'<span style="font-size: 0.65rem; font-weight: 700; color: var(--studio-muted); letter-spacing: 0.06em; text-transform: uppercase; margin-top: 2px;">{total_lbl}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
        f'<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 8px; flex: 1; min-width: 260px;">'
        f'{badges_html}'
        f'</div>'
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
    all_ngsl = set().union(*(_words(row.get(field)) for field in ("target_words", "bonus_words", "reused_words")))
    render_domain_breakdown_section(db.compute_domain_breakdown(sorted(all_ngsl)), title="Domain breakdown", compact=True)
    snapshot = parse_refinement_snapshot(row.get("refinement_report"))
    if snapshot and not report_matches_lyrics(snapshot, lyrics):
        st.caption("Authenticity refers to the archived lyrics. Open Critic to review the evaluated version.")

    with st.container(border=True):
        c_cat, c_genre, c_struct = st.columns([1.2, 1, 1.4])
        with c_cat:
            st.markdown(":material/category: **Song category**")
            dom = row.get("source_domain") or "Not tagged"
            cfg = DOMAIN_CONFIG.get(dom, {})
            emoji = cfg.get("emoji", "🏷️") if dom != "Not tagged" else "🏷️"
            st.write(f"{emoji} {dom}")
        with c_genre:
            st.markdown(":material/tune: **Musical Genre**")
            st.write(row.get("genre") or "Genre not recorded")
        with c_struct:
            st.markdown(":material/account_tree: **Structure**")
            st.write(row.get("song_structure") or "Structure not recorded")

    col_story_en, col_story_ar = st.columns(2)
    with col_story_en:
        with st.container(border=True):
            story_text = (row.get("creative_concept") or "").strip()
            hdr_col, copy_col = st.columns([1.5, 1], vertical_alignment="center")
            with hdr_col:
                st.markdown(":material/lightbulb: **The story**")
            with copy_col:
                if story_text:
                    render_simple_copy_button(
                        text=story_text,
                        label="Copy Story",
                        copied_label="Copied!",
                        button_id=f"story_{song_id}",
                        align="flex-end",
                    )
            st.markdown(
                f'<div class="story-scroll-box">'
                f'{escape(story_text or "No story concept recorded yet.")}'
                f'</div>',
                unsafe_allow_html=True,
            )
    with col_story_ar:
        with st.container(border=True):
            story_ar = (row.get("story_arabic") or "").strip()
            if story_ar:
                hdr_ar, copy_ar = st.columns([1.5, 1], vertical_alignment="center")
                with hdr_ar:
                    st.markdown(":material/translate: **قصة الأغنية (بالعربية)**")
                with copy_ar:
                    render_simple_copy_button(
                        text=story_ar,
                        label="نسخ القصة",
                        copied_label="تم النسخ!",
                        button_id=f"story_ar_{song_id}",
                        align="flex-end",
                    )
                st.markdown(
                    f'<div class="story-scroll-box" dir="rtl" style="text-align: right; font-size: 0.95rem;">'
                    f'{escape(story_ar)}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(":material/translate: **قصة الأغنية (بالعربية)**")
                st.info("لم تتم إضافة ترجمة عربية للقصة بعد. يمكنك لصقها لأول مرة أدناه، ولا يمكن تعديلها لاحقاً إلا من تبويب Edit.")
                if st.button("➕ إضافة / لصق القصة بالعربية", key=f"btn_add_story_ar_{song_id}", type="primary", width="stretch"):
                    from presentation.components.dialogs import add_story_arabic_dialog
                    add_story_arabic_dialog(song_id, row.get("title", ""))

    mood = row.get("mood_breakdown")
    if isinstance(mood, str):
        try:
            mood = json.loads(mood)
        except (ValueError, TypeError):
            mood = None
    values = {}
    if isinstance(mood, dict):
        values = {key: val for key, val in mood.items() if isinstance(val, (float, int))}

    if values:
        with st.expander(":material/auto_awesome: Mood & musical analysis", expanded=False):
            frame = pd.DataFrame(values.items(), columns=["Mood", "Percentage"]).sort_values("Percentage", ascending=False)
            st.bar_chart(frame.set_index("Mood"), horizontal=True, height=220)
    name = "".join(c for c in row["title"] if c.isalnum() or c in " _-").strip().replace(" ", "_")
    line_count = sum(bool(line.strip()) for line in lyrics.splitlines())
    suno_lyrics = (row.get("suno_lyrics") or "").strip()

    col_orig, col_suno = st.columns(2)
    with col_orig:
        with st.expander(f":material/lyrics: Original Lyrics · {line_count} lines", expanded=False):
            render_library_lyrics_copy_toolbar(title=row.get("title", ""), lyrics=lyrics, song_id=f"in_{song_id}", align="flex-start")
            with st.container(height=360):
                st.html(f'<div class="library-lyrics">{format_lyrics_with_tags(lyrics)}</div>')
        c_copy1, c_dl1 = st.columns([2, 1], vertical_alignment="center")
        with c_copy1:
            render_library_lyrics_copy_toolbar(title=row.get("title", ""), lyrics=lyrics, song_id=f"out_{song_id}", align="flex-start")
        with c_dl1:
            st.download_button("Download", data=lyrics, file_name=f"{name or 'song'}.txt", mime="text/plain", icon=":material/download:", key=f"dl_song_{song_id}", width="stretch")

    with col_suno:
        if suno_lyrics:
            suno_count = sum(bool(line.strip()) for line in suno_lyrics.splitlines())
            with st.expander(f":material/graphic_eq: Suno Lyrics · {suno_count} lines", expanded=False):
                render_library_lyrics_copy_toolbar(
                    title=row.get("title", ""),
                    lyrics=suno_lyrics,
                    song_id=f"in_suno_{song_id}",
                    align="flex-start",
                    primary_label="Copy Title & Suno",
                    secondary_label="Suno Only",
                )
                with st.container(height=360):
                    st.html(f'<div class="library-lyrics">{format_lyrics_with_tags(suno_lyrics)}</div>')
            c_copy2, c_dl2 = st.columns([2, 1], vertical_alignment="center")
            with c_copy2:
                render_library_lyrics_copy_toolbar(
                    title=row.get("title", ""),
                    lyrics=suno_lyrics,
                    song_id=f"out_suno_{song_id}",
                    align="flex-start",
                    primary_label="Copy Title & Suno",
                    secondary_label="Suno Only",
                )
            with c_dl2:
                st.download_button("Download", data=suno_lyrics, file_name=f"{name or 'song'}_suno.txt", mime="text/plain", icon=":material/download:", key=f"dl_suno_{song_id}", width="stretch")
        else:
            with st.expander(":material/graphic_eq: Suno Lyrics · Not added", expanded=False):
                st.info("No Suno lyrics saved yet. Click below to paste them for the first time. Once saved, edits can be made from the Edit tab.")
                if st.button("➕ Paste / Add Suno lyrics", key=f"btn_add_suno_{song_id}", type="primary", width="stretch"):
                    from presentation.components.dialogs import add_suno_lyrics_dialog
                    add_suno_lyrics_dialog(song_id, row.get("title", ""))

    is_suno_done = bool(row.get("is_suno_completed", 0))

    def _toggle_suno_status():
        val = st.session_state[f"chk_suno_status_{song_id}"]
        db.update_suno_status(song_id, val)
        st.session_state["library_selected_song"] = song_id
        st.session_state["lib_toast_msg"] = "Marked as produced on Suno! 🎵" if val else "Unmarked Suno completion status."

    with st.container(border=True):
        st.checkbox(
            "🎵 **Produced on Suno** (تم إنتاجها على سونو)",
            value=is_suno_done,
            key=f"chk_suno_status_{song_id}",
            on_change=_toggle_suno_status,
            help="Check this box when you have finished generating this song on Suno."
        )


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
        suno_flag = "  ·  ✅ Suno" if r.get("is_suno_completed") else ""
        return f"#{r['row_num']} • {r['title']}  ·  {words_txt}  ·  {emoji} {dom}{suno_flag}"

    options_list = list(records)
    if "library_selected_song" not in st.session_state or st.session_state["library_selected_song"] not in options_list:
        st.session_state["library_selected_song"] = options_list[0]

    selected = st.selectbox(
        "Open a song",
        options=options_list,
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
    suno_badge = ' <span style="background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.35); padding: 1px 7px; border-radius: 10px; font-size: 0.74rem; font-weight: 700; display: inline-flex; align-items: center; gap: 3px; vertical-align: middle; margin-left: 6px;">🎵 Suno Done</span>' if row.get("is_suno_completed") else ""
    st.html(f'''<article class="library-song-card" id="library-song-hero-card">
<div class="library-song-heading"><span class="library-song-mark">{icon_svg()}</span><div>
<div class="studio-eyebrow">SONG {int(row['row_num']):02d} / AUDINGO</div>
<h3>{escape(row['title'])}{suno_badge}</h3><p>{escape(row.get('genre') or 'Your original song')} · {escape(str(date))} · Cairo</p>
</div></div><div class="library-song-stats">{stats}</div></article>''')
    render_floating_library_song_fab(
        song_id=selected,
        row_num=int(row["row_num"]),
        title=row["title"],
        is_suno_completed=bool(row.get("is_suno_completed")),
    )
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
