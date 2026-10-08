"""
dialogs.py — Modal confirmation dialogs for deleting songs, deleting variants, and overwriting packages.
"""

import streamlit as st
import db
import gemini_client


@st.dialog("⚠️ Confirm Song Deletion")
def confirm_delete_song_dialog(song_id: int, song_title: str, row_num: int):
    """Safety confirmation modal before executing atomic delete and rollback."""
    st.markdown(f"#### :material/delete: Are you sure you want to delete Song #{row_num}?")
    st.warning(
        f"**Song Title:** {song_title}\n\n"
        f"⚠️ **Atomic Safe Rollback will occur:**\n"
        f"- Target & Bonus vocabulary will have their `usage_count` decremented (-1) in the NGSL dictionary.\n"
        f"- Non-NGSL extra words will have their occurrences decremented (-1).\n"
        f"- The song and all its recorded metadata will be permanently removed."
    )
    dlg_c1, dlg_c2 = st.columns(2)
    with dlg_c1:
        if st.button("🔥 Yes, Confirm Delete", type="primary", width="stretch", key=f"dlg_confirm_del_{song_id}"):
            if db.delete_song(song_id, rollback_words=True):
                st.session_state["lib_toast_msg"] = f"Song #{row_num} ('{song_title}') deleted and dictionary counters rolled back."
                st.rerun()
    with dlg_c2:
        if st.button(":material/cancel: Cancel", width="stretch", key=f"dlg_cancel_del_{song_id}"):
            st.rerun()


@st.dialog("⚠️ Confirm Track Variant Deletion")
def confirm_delete_variant_dialog(variant_id: int, genre: str, vocalist: str):
    """Safety confirmation modal before deleting a track variant package."""
    st.markdown("#### :material/delete: Delete Track Variant Package?")
    st.warning(
        f"Are you sure you want to delete the production package for **{genre}** ({vocalist})?\n\n"
        f"This will permanently delete both the Suno music prompt and the poster art prompt. This action cannot be undone."
    )
    dlg_c1, dlg_c2 = st.columns(2)
    with dlg_c1:
        if st.button("🔥 Yes, Delete Variant", type="primary", width="stretch", key=f"dlg_confirm_del_variant_{variant_id}"):
            if db.delete_track_variant(variant_id):
                st.session_state["lib_toast_msg"] = f"Track variant for '{genre}' ({vocalist}) was deleted."
                st.rerun()
    with dlg_c2:
        if st.button(":material/cancel: Cancel", width="stretch", key=f"dlg_cancel_del_variant_{variant_id}"):
            st.rerun()


@st.dialog("⚠️ Warning: Style Package Already Exists")
def confirm_overwrite_variant_dialog(song_id: int, song_title: str, lyrics_text: str, genre: str, vocalist: str):
    """Safety confirmation modal before overwriting an existing track variant."""
    st.markdown("#### ⚠️ Style Package Already Exists!")
    st.warning(
        f"A production package for **'{song_title}'** in **{genre}** with **{vocalist}** vocals already exists.\n\n"
        f"Generating a new package will **overwrite** both the current Suno music prompt and Midjourney/DALL-E poster prompt with freshly generated versions.\n\n"
        f"Are you sure you want to proceed and overwrite?"
    )
    dlg_c1, dlg_c2 = st.columns(2)
    clean_g = "".join(c for c in genre if c.isalnum())
    with dlg_c1:
        if st.button("⚡ Yes, Overwrite & Regenerate", type="primary", width="stretch", key=f"dlg_confirm_ovr_{song_id}_{clean_g}_{vocalist}"):
            with st.spinner(f"Generating new package for '{genre}' ({vocalist})..."):
                res = gemini_client.generate_track_variant(
                    title=song_title,
                    lyrics=lyrics_text,
                    genre=genre,
                    vocalist=vocalist
                )
                if res.get("success"):
                    new_suno_p = res.get("suno_prompt", "").strip()
                    new_poster_p = res.get("poster_prompt", "").strip()
                    db.upsert_track_variant(
                        song_id=song_id,
                        genre=genre,
                        vocalist=vocalist,
                        suno_prompt=new_suno_p,
                        poster_prompt=new_poster_p
                    )
                    st.session_state["lib_toast_msg"] = f"Track package for '{genre}' ({vocalist}) overwritten & updated!"
                    st.rerun()
                else:
                    st.error(f"Failed to generate package: {res.get('error')}")
    with dlg_c2:
        if st.button(":material/cancel: Cancel", width="stretch", key=f"dlg_cancel_ovr_{song_id}_{clean_g}_{vocalist}"):
            st.rerun()


def execute_studio_action(action: str):
    """Executes the requested studio action cleanly, ensuring state synchronization."""
    from presentation.components.session import set_target_batch, sync_active_session

    active_domain = st.session_state.get("selected_domain", "All Domains")
    active_blend = st.session_state.get("blend_joker", True)

    if action == "random":
        new_batch = db.pull_20_words(domain=active_domain, blend_joker=active_blend)
        if len(new_batch) == 20:
            set_target_batch(new_batch)
            st.session_state.mood_analysis = None
            st.session_state.master_prompt = ""
            st.session_state.studio_suno_prompt = ""
            st.session_state.custom_concept = ""
            st.session_state.graph_report = None
            st.session_state.word_fit_audit = None
            sync_active_session()
            if active_domain not in ("All Domains", "Basic / Neutral"):
                mode_str = " (50% Domain + 50% Joker blend)" if active_blend else " (100% Pure Domain)"
                dom_tag = f" from {active_domain}{mode_str}"
            elif active_domain == "Basic / Neutral":
                dom_tag = " from Basic / Neutral (Joker)"
            else:
                dom_tag = ""
            st.session_state["studio_toast_msg"] = f"Pulled 20 random unused words (10 Nouns, 6 Verbs, 4 Adjectives){dom_tag}!"
            st.rerun()
        elif len(new_batch) > 0:
            set_target_batch(new_batch)
            st.session_state.custom_concept = ""
            st.session_state.studio_suno_prompt = ""
            st.session_state.graph_report = None
            st.session_state.word_fit_audit = None
            sync_active_session()
            st.warning(f"Only {len(new_batch)} unused words available in database.")
            st.rerun()
        else:
            st.error("No unused words remaining in the database!")

    elif action == "smart_pull":
        dom_spin = f" within {active_domain}" if active_domain != "All Domains" else ""
        with st.spinner(f"🧠 Gemini is curating a cohesive 20-word batch{dom_spin}..."):
            candidate_pool = db.pull_candidate_pool_for_thematic_curation(
                nouns_limit=70,
                verbs_limit=40,
                adjs_limit=30,
                domain=active_domain,
                blend_joker=active_blend
            )
            candidate_nouns = [w["word"] for w in candidate_pool["Noun"]]
            candidate_verbs = [w["word"] for w in candidate_pool["Verb"]]
            candidate_adjs = [w["word"] for w in candidate_pool["Adjective"]]

            curation_res = gemini_client.curate_thematic_vocabulary_batch(
                candidate_nouns=candidate_nouns,
                candidate_verbs=candidate_verbs,
                candidate_adjs=candidate_adjs,
                domain_focus=active_domain
            )

            curated_batch = db.build_curated_batch_from_words(
                selected_nouns=curation_res.get("selected_nouns", []),
                selected_verbs=curation_res.get("selected_verbs", []),
                selected_adjs=curation_res.get("selected_adjectives", []),
                candidate_pool=candidate_pool
            )

            if len(curated_batch) == 20:
                set_target_batch(curated_batch)
                st.session_state.mood_analysis = None
                st.session_state.master_prompt = ""
                st.session_state.studio_suno_prompt = ""
                st.session_state.custom_concept = curation_res.get("theme_description", "")
                st.session_state.graph_report = None
                st.session_state.word_fit_audit = None
                sync_active_session()
                theme_title = curation_res.get("theme_name", "Curated Storyline")
                st.session_state["studio_toast_msg"] = f"✨ Curated 20 thematic words for '{theme_title}' (10 Nouns, 6 Verbs, 4 Adjectives)!"
                st.rerun()
            elif len(curated_batch) > 0:
                set_target_batch(curated_batch)
                st.session_state.custom_concept = curation_res.get("theme_description", "")
                st.session_state.graph_report = None
                st.session_state.word_fit_audit = None
                sync_active_session()
                st.warning(f"Curated {len(curated_batch)} words.")
                st.rerun()
            else:
                st.error("Could not curate a batch from unused words.")

    elif action == "redraw":
        new_batch = db.pull_20_words(domain=active_domain, blend_joker=active_blend)
        set_target_batch(new_batch)
        st.session_state.mood_analysis = None
        st.session_state.master_prompt = ""
        st.session_state.studio_suno_prompt = ""
        st.session_state.custom_concept = ""
        st.session_state.graph_report = None
        st.session_state.word_fit_audit = None
        sync_active_session()
        st.session_state["studio_toast_msg"] = "Batch redrawn with 20 fresh words."
        st.rerun()

    elif action == "clear":
        set_target_batch([])
        st.session_state.mood_analysis = None
        st.session_state.master_prompt = ""
        st.session_state.studio_suno_prompt = ""
        st.session_state.custom_concept = ""
        st.session_state.graph_report = None
        st.session_state.word_fit_audit = None
        db.clear_active_batch_state()
        st.session_state["studio_toast_msg"] = "Target batch cleared."
        st.rerun()


@st.dialog("⚠️ تنبيه: جلسة عمل نشطة (Confirm Reset)")
def confirm_studio_reset_dialog(action: str):
    """Safety confirmation modal before resetting or replacing active studio session."""
    action_titles = {
        "random": "🎲 Random 20 (سحب 20 كلمة عشوائية)",
        "smart_pull": "🧠 Smart Thematic Pull (سحب ثيماتي ذكي)",
        "redraw": "🔄 Cancel & Redraw (إلغاء وإعادة السحب)",
        "clear": "🧹 Clear (مسح الدفعة الحالية)"
    }
    action_name = action_titles.get(action, action)

    has_lyrics = any(
        bool(st.session_state.get(k, "").strip())
        for k in ("refine_draft", "commit_lyrics", "raw_lyrics_input")
    )
    has_title = any(
        bool(st.session_state.get(k, "").strip())
        for k in ("song_title_input", "commit_song_title_input_field")
    )
    has_concept = bool(st.session_state.get("custom_concept", "").strip())
    has_prompt = bool(st.session_state.get("master_prompt", "").strip())
    batch_count = len(st.session_state.get("target_batch", []))

    st.markdown(f"#### ⚠️ أنت تعمل على أغنية بالفعل!")
    st.markdown(
        f"الضغط على **{action_name}** سيؤدي إلى **إعادة تعيين الجلسة الحالية** واستبدال الكلمات أو مسحها، "
        f"مما قد يتسبب في فقدان المسودات والإعدادات غير المحفوظة."
    )

    details = []
    if batch_count > 0:
        details.append(f"• **الدفعة الحالية:** {batch_count} كلمة مستهدفة قيد الاستخدام")
    if has_lyrics:
        details.append("• **مسودة الكلمات:** يوجد نص أو مسودة أغنية مكتوبة")
    if has_title:
        title = st.session_state.get("song_title_input") or st.session_state.get("commit_song_title_input_field")
        details.append(f"• **عنوان الأغنية:** '{title}'")
    if has_concept:
        details.append("• **قصة الأغنية / الفكرة الإبداعية:** محددة ومحفوظة")
    if has_prompt:
        details.append("• **برومبت كتابة الأغنية:** تم تجهيزه بالفعل")

    if details:
        st.warning("\n".join(details))

    st.info("هل أنت متأكد أنك تريد المتابعة وبدء عمل جديد؟ اضغط **OK** للتنفيذ أو **Cancel** للحفاظ على شغلك.")

    dlg_c1, dlg_c2 = st.columns(2)
    with dlg_c1:
        if st.button(":material/check: OK, Proceed", type="primary", width="stretch", key=f"dlg_ok_reset_{action}"):
            st.session_state.pop("pending_studio_reset_action", None)
            execute_studio_action(action)
    with dlg_c2:
        if st.button(":material/cancel: Cancel", width="stretch", key=f"dlg_cancel_reset_{action}"):
            st.session_state.pop("pending_studio_reset_action", None)
            st.rerun()

