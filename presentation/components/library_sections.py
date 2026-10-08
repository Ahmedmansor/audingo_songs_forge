"""Production tools and editing, rendered only when selected in Library."""

import streamlit as st
import db
import gemini_client
from constants import GENRES, SONG_STRUCTURES
from presentation.components.dialogs import (
    confirm_delete_song_dialog, confirm_delete_variant_dialog, confirm_overwrite_variant_dialog,
)


def render_library_production(row):
    song_id = int(row["id"])
    title = row["title"]
    lyrics = row["lyrics"] or ""
    variants = db.get_track_variants(song_id)
    st.markdown("##### :material/graphic_eq: Production packages")
    st.caption("Music style and cover artwork, paired for each version of your song.")
    if variants:
        records = {int(variant["id"]): variant for variant in variants}
        selected = st.selectbox("Saved package", list(records),
            format_func=lambda variant_id: f"{records[variant_id]['genre']} · {records[variant_id]['vocalist']}",
            key=f"library_package_{song_id}")
        variant = records[selected]
        with st.container(border=True):
            st.caption(f"{variant['genre']} · {variant['vocalist']} · {variant['created_at']}")
            prompt = st.segmented_control("Production prompt", ["Music", "Cover"], default="Music", required=True,
                key=f"package_prompt_{selected}", format_func=lambda name: f":material/{'music_note' if name == 'Music' else 'palette'}: {name}")
            st.code(variant["suno_prompt"] if prompt == "Music" else variant["poster_prompt"], language=None, wrap_lines=True)
            with st.expander(":material/edit_note: Edit package", expanded=False):
                with st.form(f"package_edit_{selected}"):
                    suno = st.text_area("Suno music style", value=variant["suno_prompt"], key=f"txt_suno_{selected}", height=100)
                    poster = st.text_area("Cover art prompt", value=variant["poster_prompt"], key=f"txt_poster_{selected}", height=160)
                    if st.form_submit_button("Save package", icon=":material/save:", type="primary"):
                        db.update_track_variant(selected, suno, poster)
                        st.session_state["lib_toast_msg"] = "Production package saved."
                        st.rerun()
            with st.container(horizontal=True):
                if st.button("Regenerate", icon=":material/refresh:", key=f"btn_regen_var_{selected}"):
                    confirm_overwrite_variant_dialog(song_id, title, lyrics, variant["genre"], variant["vocalist"])
                if st.button("Delete package", icon=":material/delete:", key=f"btn_del_var_{selected}"):
                    confirm_delete_variant_dialog(selected, variant["genre"], variant["vocalist"])
    else:
        st.info("No production packages yet. Create your first version below.")
    with st.expander(":material/add_circle: Create a production package", expanded=False):
        left, right = st.columns([2, 1])
        genre_val = row.get("genre") or ""
        genre = left.selectbox("Genre", GENRES, index=GENRES.index(genre_val) if genre_val in GENRES else 0, key=f"variant_genre_{song_id}")
        vocalist = right.selectbox("Lead vocalist", ["Male", "Female", "Duet", "Instrumental"], key=f"variant_vocalist_{song_id}")
        if st.button("Generate package", icon=":material/auto_awesome:", key=f"btn_gen_variant_{song_id}", type="primary"):
            if db.get_track_variant_by_combo(song_id, genre, vocalist):
                confirm_overwrite_variant_dialog(song_id, title, lyrics, genre, vocalist)
            else:
                with st.spinner("Creating music and artwork prompts…"):
                    result = gemini_client.generate_track_variant(title=title, lyrics=lyrics, genre=genre, vocalist=vocalist)
                    if result.get("success"):
                        db.upsert_track_variant(song_id, genre, vocalist, result.get("suno_prompt", "").strip(), result.get("poster_prompt", "").strip())
                        st.session_state["lib_toast_msg"] = "Production package created."
                        st.rerun()
                    else:
                        st.error(f"Could not create package: {result.get('error')}")


def render_library_editor(row):
    song_id = int(row["id"])
    row_num = int(row["row_num"])
    song_title = row["title"]
    lyrics_text = row["lyrics"] or ""
    genre_val = row.get("genre") or ""
    structure_val = row.get("song_structure") or ""
    concept_val = row.get("creative_concept") or ""
    target_words_raw = row.get("target_words") or ""
    bonus_words_raw = row.get("bonus_words") or ""
    reused_words_raw = row.get("reused_words") or ""
    extra_words_raw = row.get("extra_words") or ""

    with st.form(key=f"edit_form_{song_id}"):
        st.markdown(f"#### Editing song #{row_num} — {song_title}")
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
            ":material/lightbulb: Story / Creative Concept (Generated by Gemini, fully editable by you):",
            value=concept_val,
            height=85,
            help="Story scenario and narrative concept for this song.",
            key=f"edit_concept_{song_id}"
        )

        new_targets = st.text_area(
            ":material/adjust: Target Words (comma-separated):",
            value=target_words_raw,
            placeholder="e.g. coffee, application, negotiate, salary, employer, client...",
            help="Primary target vocabulary for this song.",
            key=f"edit_targets_{song_id}"
        )

        e_w_col1, e_w_col2, e_w_col3 = st.columns(3)
        with e_w_col1:
            new_bonuses = st.text_area(
                "Bonus NGSL words (comma-separated)",
                value=bonus_words_raw,
                placeholder="Incidental new NGSL words found in song...",
                help="New incidental words from NGSL introduced in this song.",
                key=f"edit_bonuses_{song_id}"
            )
        with e_w_col2:
            new_reused = st.text_area(
                "Previously covered words:",
                value=reused_words_raw,
                placeholder="NGSL words previously covered...",
                help="NGSL words already introduced in earlier songs.",
                key=f"edit_reused_{song_id}"
            )
        with e_w_col3:
            new_extras = st.text_area(
                "Extra words (comma-separated):",
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

        save_btn = st.form_submit_button(":material/save: Save updates", type="primary", width="stretch")
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

    st.markdown("##### :material/auto_awesome: Re-analyze Mood & Story with Gemini:")
    if st.button(f":material/auto_awesome: Run Gemini Mood & Story Analysis on Target Words", key=f"gemini_reanalyze_{song_id}"):
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

    with st.expander(":material/delete: Delete this song", expanded=False):
        st.caption("Deleting removes the song and its production packages, and rolls back its vocabulary counters.")
        if st.button("Delete song", icon=":material/delete:", key=f"del_song_{song_id}"):
            confirm_delete_song_dialog(song_id, song_title, row_num)
