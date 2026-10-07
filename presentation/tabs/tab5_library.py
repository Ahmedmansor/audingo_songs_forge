"""
tab4_library.py — Tab 4: Songs Library & Archives.
"""

import json
import pandas as pd
import streamlit as st
from constants import GENRES, SONG_STRUCTURES, DOMAIN_CONFIG
import db
import gemini_client
from presentation.components.widgets import (
    format_cairo_display_time,
    render_domain_breakdown_section,
)
from presentation.components.dialogs import (
    confirm_delete_song_dialog,
    confirm_delete_variant_dialog,
    confirm_overwrite_variant_dialog,
)


def render_tab_library():
    """Renders the Saved Songs Library, Vocabulary Breakdown, Track Variants, and In-Place Editor."""
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
        songs_df = songs_df.reset_index(drop=True)
        songs_df["row_num"] = songs_df["id"].rank(method="dense", ascending=True).astype(int)

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

            song_all_ngsl = list(set(target_list + bonus_list + reused_list))
            song_domain_data = db.compute_domain_breakdown(song_all_ngsl)
            primary_dom = song_domain_data.get("primary_domain", "Basic / Neutral")
            primary_pct = song_domain_data.get("primary_percent", 0.0)
            primary_cfg = DOMAIN_CONFIG.get(primary_dom, {})
            primary_emoji = primary_cfg.get("emoji", "🎵")

            mood_dict = {}
            if mood_raw:
                try:
                    mood_dict = json.loads(mood_raw) if isinstance(mood_raw, str) else mood_raw
                except Exception:
                    mood_dict = {}

            display_time = format_cairo_display_time(created_at)
            total_new_words = len(target_list) + len(bonus_list)

            with st.expander(
                f"🎵 #{row_num} — **{song_title}** ｜ 🔥 **+{total_new_words} New NGSL** (🟢 {len(target_list)} + 🔵 {len(bonus_list)}) ｜ ⚪ {len(reused_list)} Reused ｜ {primary_emoji} **{primary_dom}** ({primary_pct}%) ｜ 📅 {display_time}",
                expanded=(loop_idx == 0)
            ):
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
                            <span class="stat-badge" style="background: {primary_cfg.get('bg', 'rgba(16,185,129,0.15)')}; color: {primary_cfg.get('color', '#34D399')}; border: 1px solid {primary_cfg.get('border', 'rgba(52,211,153,0.4)')}; font-weight: 700;">
                                {primary_emoji} {primary_dom} ({primary_pct}%)
                            </span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                info_col1, info_col2 = st.columns([3, 1])
                with info_col1:
                    st.markdown(f"**🎯 Target Vocabulary ({len(target_list)}):**")
                    if target_list:
                        pills_html = " ".join(f'<span class="target-pill">{w}</span>' for w in target_list)
                        st.markdown(pills_html, unsafe_allow_html=True)
                    else:
                        st.error("⚠️ Target words are empty! Click '✏️ Edit Song Details, Words & Metadata' below to add them by hand.")

                    if bonus_list:
                        st.markdown(f"<div style='margin-top: 8px;'><b>🔵 Bonus NGSL Hits ({len(bonus_list)}):</b></div>", unsafe_allow_html=True)
                        bonus_html = " ".join(f'<span class="bonus-pill">{w}</span>' for w in bonus_list)
                        st.markdown(bonus_html, unsafe_allow_html=True)

                    if reused_list:
                        st.markdown(f"<div style='margin-top: 8px;'><b>⚪ Previously Covered Words ({len(reused_list)}):</b></div>", unsafe_allow_html=True)
                        reused_html = " ".join(f'<span class="reused-pill">{w}</span>' for w in reused_list)
                        st.markdown(reused_html, unsafe_allow_html=True)

                    if extra_list:
                        st.markdown(f"<div style='margin-top: 8px;'><b>🟡 Extra Words ({len(extra_list)}):</b></div>", unsafe_allow_html=True)
                        extra_html = " ".join(f'<span class="extra-pill">{w}</span>' for w in extra_list)
                        st.markdown(extra_html, unsafe_allow_html=True)

                    render_domain_breakdown_section(
                        song_domain_data,
                        title="🎯 Song Vocabulary Domain Register",
                        compact=False
                    )

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

                st.markdown("##### 🤖 Step 2: Gemini Flash Mood & Musical Analysis:")
                
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

                # Track Variants & Packaging (Suno + Poster)
                saved_variants = db.get_track_variants(song_id)
                variants_count = len(saved_variants)
                variant_expander_title = f"💿 Track Variants & Packaging ({variants_count})" if variants_count > 0 else "💿 Track Variants & Packaging"

                with st.expander(variant_expander_title, expanded=(variants_count > 0)):
                    st.markdown("##### 💿 Audio & Visual Production Package (Suno AI + Midjourney/DALL-E)")
                    st.caption(
                        "Generate unified style variations (Covers) for this song with a single click: a keyword-optimized music style prompt for Suno AI (< 120 chars, BPM, vocal clarity) paired with an aesthetic album cover prompt for Midjourney / DALL-E featuring artistic typography."
                    )

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
