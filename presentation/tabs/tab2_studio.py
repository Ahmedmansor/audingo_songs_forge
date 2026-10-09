"""
tab2_studio.py — Tab 2: Studio (Word Selection & Prompt Generation).
"""

import streamlit as st
import pandas as pd
from constants import GENRES, SONG_STRUCTURES, DOMAINS, DOMAIN_CONFIG
import db
import prompt_builder
import gemini_client
from presentation.components.widgets import (
    render_copy_words_toolbar,
    render_domain_breakdown_section,
    render_floating_audit_prompt_fab,
)
from presentation.components.session import sync_active_session, set_target_batch
from presentation.components.dialogs import confirm_studio_reset_dialog, execute_studio_action


def is_active_song_in_progress() -> bool:
    """
    Returns True if user has an active song session in progress (target batch, lyrics, concept, prompt, etc.).
    Protects against accidental reset/clear clicks.
    """
    has_batch = bool(st.session_state.get("target_batch"))
    has_lyrics = any(
        bool(st.session_state.get(k, "").strip())
        for k in ("refine_draft", "commit_lyrics", "raw_lyrics_input")
    )
    has_title = any(
        bool(st.session_state.get(k, "").strip())
        for k in ("song_title_input", "commit_song_title_input_field")
    )
    has_concept_or_prompt = any(
        bool(st.session_state.get(k, "").strip())
        for k in ("custom_concept", "master_prompt", "studio_suno_prompt")
    )
    has_reports = any(
        bool(st.session_state.get(k))
        for k in ("graph_report", "critic_only_report", "word_fit_audit")
    )
    return has_batch or has_lyrics or has_title or has_concept_or_prompt or has_reports


def render_tab_studio():
    """Renders the Target Word Selection, Batch Management, and AI Prompt Generator."""
    if st.session_state.get("studio_toast_msg"):
        st.toast(st.session_state.pop("studio_toast_msg"))

    active_target_words = [w["word"] for w in st.session_state.target_batch] if st.session_state.get("target_batch") else []
    render_floating_audit_prompt_fab(active_target_words)

    st.subheader("Make room for your next idea.")
    st.caption("Choose your words, shape the mood, and craft your song.")

    # ─── Approved Session Drafts — Recovery Dropdown ───────────────────────────────────
    _all_drafts = db.list_studio_drafts()
    if _all_drafts:
        with st.expander(":material/folder_open: Load from Approved Session Drafts (last 10)", expanded=False):
            st.caption(
                "These snapshots were saved automatically each time you approved a song. "
                "Load one to restore its word batch and re-use it as a starting point."
            )
            _draft_options = {
                f"🎵 \u2018{d['song_title']}\u2019 — {d['label']} ({d['saved_at'][:16]})": d['id']
                for d in _all_drafts
            }
            _selected_label = st.selectbox(
                "Select a draft to preview or load:",
                options=list(_draft_options.keys()),
                index=0,
                key="draft_selector"
            )
            _selected_draft_id = _draft_options[_selected_label]

            _draft_payload = db.load_studio_draft(_selected_draft_id)
            _draft_batch = _draft_payload.get("target_batch", [])

            if _draft_batch:
                st.markdown(
                    "**Words in this draft:** " +
                    " ".join(
                        f"`{w['word']}`" for w in _draft_batch
                    )
                )

            _dc1, _dc2, _dc3 = st.columns([2, 2, 1])
            with _dc1:
                if st.button(":material/restore: Load Draft (words only)", width="stretch", key="btn_load_draft_words"):
                    if _draft_batch:
                        set_target_batch(_draft_batch)
                        st.session_state.mood_analysis = None
                        st.session_state.master_prompt = ""
                        st.session_state.studio_suno_prompt = ""
                        st.session_state.studio_poster_prompt = ""
                        st.session_state.custom_concept = ""
                        st.session_state.graph_report = None
                        sync_active_session()
                        st.success("✅ Word batch restored from draft!")
                        st.rerun()
                    else:
                        st.warning("This draft has no words saved.")
            with _dc2:
                if st.button(":material/inventory_2: Load Draft (full session)", width="stretch", key="btn_load_draft_full"):
                    if _draft_payload:
                        set_target_batch(_draft_batch)
                        st.session_state.mood_analysis = _draft_payload.get("mood_analysis", None)
                        st.session_state.master_prompt = _draft_payload.get("master_prompt", "")
                        st.session_state.studio_suno_prompt = _draft_payload.get("suno_prompt", "")
                        st.session_state.studio_poster_prompt = _draft_payload.get("poster_prompt", "")
                        st.session_state.custom_concept = _draft_payload.get("custom_concept", "")
                        st.session_state.graph_report = None
                        st.session_state.selected_genre = _draft_payload.get("selected_genre", st.session_state.selected_genre)
                        st.session_state.selected_structure = _draft_payload.get("selected_structure", st.session_state.selected_structure)
                        st.session_state.selected_vocalist = _draft_payload.get("selected_vocalist", st.session_state.selected_vocalist)
                        sync_active_session(invalidate_direction=False)
                        st.success("✅ Full session restored from draft!")
                        st.rerun()
                    else:
                        st.warning("Could not load this draft.")
            with _dc3:
                if st.button(":material/delete: Delete", width="stretch", key="btn_delete_draft"):
                    db.delete_studio_draft(_selected_draft_id)
                    st.success("Draft deleted.")
                    st.rerun()

    # ─── Domain Filter Selector ───────────────────────────────────────
    studio_dom_stats = db.get_domain_detailed_stats()
    total_uns_all = sum(d["unused"] for d in studio_dom_stats.values())
    all_dom_label = f"🌐 All Domains ({total_uns_all:,} Remaining - General Draw)"

    domain_options = [all_dom_label] + [
        f"{d} ({studio_dom_stats.get(d, {}).get('unused', 0):,} remaining / {studio_dom_stats.get(d, {}).get('total', 0):,})"
        for d in DOMAINS
    ]
    domain_key_map = {all_dom_label: "All Domains"}
    domain_label_from_key = {"All Domains": all_dom_label}
    for d in DOMAINS:
        lbl = f"{d} ({studio_dom_stats.get(d, {}).get('unused', 0):,} remaining / {studio_dom_stats.get(d, {}).get('total', 0):,})"
        domain_key_map[lbl] = d
        domain_label_from_key[d] = lbl

    current_selected_domain = st.session_state.get("selected_domain", "All Domains")
    default_domain_label = domain_label_from_key.get(current_selected_domain, all_dom_label)
    default_idx = domain_options.index(default_domain_label) if default_domain_label in domain_options else 0

    col_filter_ui, col_joker_toggle, col_filter_badge = st.columns([1.6, 1.1, 1.3], vertical_alignment="center")
    with col_filter_ui:
        chosen_domain_label = st.selectbox(
            ":material/adjust: Filter by Vocabulary Domain:",
            options=domain_options,
            index=default_idx,
            key="studio_domain_selector",
            help="Select a specific domain to pull words exclusively from that category, or select All Domains for general random draw."
        )
        new_domain_val = domain_key_map[chosen_domain_label]
        if new_domain_val != st.session_state.selected_domain:
            st.session_state.selected_domain = new_domain_val
            sync_active_session()
            st.rerun()

    with col_joker_toggle:
        if new_domain_val not in ("All Domains", "Basic / Neutral"):
            blend_joker = st.checkbox(
                "🃏 دمج الجوكر (50% Joker)",
                value=st.session_state.get("blend_joker", True),
                key="chk_blend_joker",
                help="عند التفعيل: يتم دمج 50% من كلمات المجال مع 50% من كلمات الجوكر (Basic / Neutral) لضمان تماسك الأغنية. عند الإلغاء: يتم سحب 100% من كلمات المجال المختار حصراً."
            )
            if blend_joker != st.session_state.get("blend_joker", True):
                st.session_state.blend_joker = blend_joker
                st.rerun()
        else:
            st.markdown(
                '<div style="margin-top: 10px; font-size: 0.78rem; color: var(--studio-muted); font-style: italic;">'
                '🃏 الجوكر مدمج تلقائياً'
                '</div>',
                unsafe_allow_html=True
            )
            blend_joker = True
            st.session_state.blend_joker = True

    with col_filter_badge:
        if new_domain_val == "All Domains":
            badge_html = (
                f'<div style="margin-top: 12px; font-size: 0.82rem; color: var(--studio-muted); background: rgba(148,163,184,0.1); '
                f'border: 1px solid rgba(148,163,184,0.25); border-radius: 8px; padding: 7px 12px;">'
                f'🎲 <b>{total_uns_all:,}</b> unused words remaining across all domains'
                f'</div>'
            )
            st.markdown(badge_html, unsafe_allow_html=True)
        elif new_domain_val == "Basic / Neutral":
            cfg = DOMAIN_CONFIG.get(new_domain_val, {})
            cur_uns = studio_dom_stats.get(new_domain_val, {}).get('unused', 0)
            cur_tot = studio_dom_stats.get(new_domain_val, {}).get('total', 0)
            badge_html = (
                f'<div style="margin-top: 12px; font-size: 0.82rem; color: {cfg.get("color", "#F59E0B")}; '
                f'background: {cfg.get("bg", "rgba(245,158,11,0.1)")}; border: 1px solid {cfg.get("border", "rgba(245,158,11,0.3)")}; '
                f'border-radius: 8px; padding: 7px 12px; font-weight: 700;">'
                f'{cfg.get("emoji", "🃏")} <b>{cur_uns:,}</b> words left &nbsp;•&nbsp; 🃏 Pure Joker Draw (100% Neutral)'
                f'</div>'
            )
            st.markdown(badge_html, unsafe_allow_html=True)
        else:
            cfg = DOMAIN_CONFIG.get(new_domain_val, {})
            cur_uns = studio_dom_stats.get(new_domain_val, {}).get('unused', 0)
            cur_tot = studio_dom_stats.get(new_domain_val, {}).get('total', 0)
            current_blend = st.session_state.get("blend_joker", True)
            mode_label = "🃏 50% Joker Blended" if current_blend else "🎯 100% Pure Domain"
            badge_html = (
                f'<div style="margin-top: 12px; font-size: 0.82rem; color: {cfg.get("color", "#38BDF8")}; '
                f'background: {cfg.get("bg", "rgba(56,189,248,0.1)")}; border: 1px solid {cfg.get("border", "rgba(56,189,248,0.3)")}; '
                f'border-radius: 8px; padding: 7px 12px; font-weight: 700;">'
                f'{cfg.get("emoji", "")} <b>{cur_uns:,}</b> left &nbsp;•&nbsp; {mode_label}'
                f'</div>'
            )
            st.markdown(badge_html, unsafe_allow_html=True)

    col_actions, _ = st.columns([2.5, 1])
    with col_actions:
        b_col1, b_col2, b_col3, b_col4 = st.columns([1.1, 1.3, 1, 0.9])
        with b_col1:
            if st.button(":material/shuffle: Random 20", type="secondary", width="stretch", help="Randomly pull 20 unused words (10 N, 6 V, 4 A) directly from SQLite."):
                if is_active_song_in_progress():
                    st.session_state["pending_studio_reset_action"] = "random"
                else:
                    execute_studio_action("random")

        with b_col2:
            if st.button(":material/neurology: Smart Thematic Pull", type="primary", width="stretch", help="Gemini analyzes 140 candidate unused words and selects 20 words (10 N, 6 V, 4 A) that share natural chemistry and relate to an authentic everyday life scenario."):
                if is_active_song_in_progress():
                    st.session_state["pending_studio_reset_action"] = "smart_pull"
                else:
                    execute_studio_action("smart_pull")

        with b_col3:
            if st.button(":material/refresh: Cancel & Redraw", width="stretch"):
                if is_active_song_in_progress():
                    st.session_state["pending_studio_reset_action"] = "redraw"
                else:
                    execute_studio_action("redraw")

        with b_col4:
            if st.button(":material/mop: Clear", width="stretch", help="Clear active target batch"):
                if is_active_song_in_progress():
                    st.session_state["pending_studio_reset_action"] = "clear"
                else:
                    execute_studio_action("clear")

        if st.session_state.get("pending_studio_reset_action"):
            confirm_studio_reset_dialog(st.session_state["pending_studio_reset_action"])

    # Display Active Batch
    if st.session_state.target_batch:
        current_words = [w["word"] for w in st.session_state.target_batch]
        current_ids = [w["id"] for w in st.session_state.target_batch]
        
        nouns_count = sum(1 for w in st.session_state.target_batch if w["pos_type"] == "Noun")
        verbs_count = sum(1 for w in st.session_state.target_batch if w["pos_type"] == "Verb")
        adjs_count = sum(1 for w in st.session_state.target_batch if w["pos_type"] == "Adjective")
        others_count = sum(1 for w in st.session_state.target_batch if w["pos_type"] not in ("Noun", "Verb", "Adjective"))

        col_batch_info, col_batch_actions = st.columns([1.25, 1.15], vertical_alignment="center")
        with col_batch_info:
            other_pill = f'<span style="background: var(--studio-neutral-bg); color: var(--studio-neutral-ink); font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; border: 1px solid var(--studio-line);">⚪ {others_count} Other</span>' if others_count else ''
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 2px;">
                    <span style="font-weight: 700; color: var(--studio-ink); font-size: 1.05rem;">🎯 Active Target Batch:</span>
                    <span style="background: var(--studio-tint); color: var(--studio-purple); font-size: 0.82rem; font-weight: 700; padding: 2px 9px; border-radius: 12px; border: 1px solid var(--studio-line);">{len(st.session_state.target_batch)} Words</span>
                    <span style="background: var(--studio-tint); color: var(--studio-blue); font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; border: 1px solid var(--studio-line);">🔵 {nouns_count} Nouns</span>
                    <span style="background: var(--studio-green-bg); color: var(--studio-green); font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; border: 1px solid var(--studio-line);">🟢 {verbs_count} Verbs</span>
                    <span style="background: var(--studio-amber-bg); color: var(--studio-amber); font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; border: 1px solid var(--studio-line);">🟡 {adjs_count} Adjectives</span>
                    {other_pill}
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_batch_actions:
            render_copy_words_toolbar(current_words)

        batch_domain_data = db.compute_domain_breakdown(current_words)
        render_domain_breakdown_section(batch_domain_data, title="📊 Active 20-Word Batch Domain Balance", compact=True)

        # Pre-Lyrics Audit Bar (Vocabulary vs Story Context)
        audit_data = st.session_state.get("word_fit_audit") or {}
        flagged_list = audit_data.get("flagged_words", [])
        flagged_dict = {
            fw.get("word", "").lower().strip(): fw.get("reason", "")
            for fw in flagged_list if fw.get("word")
        }

        st.markdown("##### :material/fact_check: Pre-Lyrics Audit (Vocabulary vs Story Context):")
        aud_col_btn, aud_col_status = st.columns([1.5, 2], vertical_alignment="center")
        with aud_col_btn:
            if st.button(
                ":material/fact_check: Audit Words vs Story Context",
                type="secondary",
                width="stretch",
                key="btn_audit_words_story",
                help="Audit the 20 target words against the story scenario to check for words that feel forced, overly technical, or out of context for everyday conversational dialogue."
            ):
                concept_val = st.session_state.custom_concept.strip() or (
                    st.session_state.mood_analysis.get("creative_concept", "").strip() if st.session_state.mood_analysis else ""
                )
                if not concept_val:
                    st.warning("💡 Please generate or write a Story / Creative Concept in Step 2 below before auditing.")
                elif not current_words:
                    st.warning("⚠️ No active target batch found.")
                else:
                    with st.spinner("🔍 Auditing 20 words against story scenario with Gemini Flash..."):
                        audit_res = gemini_client.audit_words_against_story(
                            current_words,
                            concept_val,
                            domain=st.session_state.selected_domain
                        )
                        st.session_state.word_fit_audit = audit_res
                        sync_active_session()
                        st.rerun()

        with aud_col_status:
            if st.session_state.get("word_fit_audit"):
                audit_info = st.session_state.word_fit_audit
                flagged_arr = audit_info.get("flagged_words", [])
                if not flagged_arr or audit_info.get("all_fit"):
                    st.success("✅ **Harmony Passed:** All 20 words fit naturally into this story scenario without forcing awkward dialogue!")
                else:
                    st.warning(f"⚠️ **{len(flagged_arr)} Word(s) Flagged:** Check the highlighted cards below to easily swap them.")

        if st.session_state.get("word_fit_audit"):
            audit_info = st.session_state.word_fit_audit
            flagged_arr = audit_info.get("flagged_words", [])
            summary_txt = audit_info.get("summary", "")
            if flagged_arr:
                with st.expander(f":material/info: View Audit Feedback ({len(flagged_arr)} Words Flagged)", expanded=False):
                    if summary_txt:
                        st.markdown(f"**Overall Assessment:** {summary_txt}")
                    for item in flagged_arr:
                        st.markdown(f"- **`{item.get('word', '')}`**: {item.get('reason', '')}")
                    if st.button(":material/close: Dismiss Audit Warnings", key="dismiss_audit_btn"):
                        st.session_state.word_fit_audit = None
                        sync_active_session()
                        st.rerun()

        # Check active checkbox selections for batch swap
        selected_indices = [
            i for i, w in enumerate(st.session_state.target_batch)
            if st.session_state.get(f"chk_swap_{w['id']}_{i}", False)
        ]
        num_selected = len(selected_indices)

        # Batch Swap Action Toolbar
        col_bswap_info, col_bswap_btn, col_bswap_quick = st.columns([1.6, 1.4, 1.2], vertical_alignment="center")
        with col_bswap_info:
            if num_selected > 0:
                st.markdown(f"**⚡ {num_selected} word(s) selected for batch swap:**")
            else:
                st.markdown("<span style='color: var(--studio-muted); font-size: 0.88rem;'>☑️ Check boxes below to swap multiple words at once:</span>", unsafe_allow_html=True)
        
        with col_bswap_btn:
            if num_selected > 0:
                if st.button(
                    f":material/swap_calls: Swap Selected ({num_selected})",
                    type="primary",
                    width="stretch",
                    key="btn_swap_selected_words",
                    help=f"Swap all {num_selected} selected words simultaneously with fresh unused words"
                ):
                    words_to_swap = [st.session_state.target_batch[i] for i in selected_indices]
                    selected_dom = st.session_state.get("selected_domain", "All Domains")
                    swap_results = db.swap_multiple_words(words_to_swap, current_ids, domain=selected_dom)

                    updated_batch = list(st.session_state.target_batch)
                    swapped_count = 0
                    swapped_names = []

                    for i in selected_indices:
                        old_w = updated_batch[i]
                        new_w = swap_results.get(old_w["id"])
                        if new_w:
                            updated_batch[i] = new_w
                            swapped_count += 1
                            dom_tag = f" [{new_w.get('domain', '')}]" if new_w.get("domain") and selected_dom != "All Domains" else ""
                            swapped_names.append(f"{old_w['word']} → {new_w['word']}{dom_tag}")
                        st.session_state.pop(f"chk_swap_{old_w['id']}_{i}", None)

                    if swapped_count > 0:
                        set_target_batch(updated_batch, keep_direction=True, clear_lyrics=False)
                        st.session_state.master_prompt = ""
                        st.session_state.studio_suno_prompt = ""
                        st.session_state.graph_report = None

                        if st.session_state.get("word_fit_audit"):
                            swapped_lowers = {w["word"].lower().strip() for w in words_to_swap}
                            cur_flagged = st.session_state.word_fit_audit.get("flagged_words", [])
                            st.session_state.word_fit_audit["flagged_words"] = [
                                fw for fw in cur_flagged if fw.get("word", "").lower().strip() not in swapped_lowers
                            ]
                        sync_active_session()
                        dom_info = f" from '{selected_dom}'" if selected_dom and selected_dom != "All Domains" else ""
                        st.success(f"✨ Swapped {swapped_count} words{dom_info}: {', '.join(swapped_names[:4])}{'...' if len(swapped_names) > 4 else ''}")
                        st.rerun()
                    else:
                        st.warning("No more unused words available to swap for the selected parts of speech.")

        with col_bswap_quick:
            flagged_unselected = [
                i for i, w in enumerate(st.session_state.target_batch)
                if w["word"].lower().strip() in flagged_dict and not st.session_state.get(f"chk_swap_{w['id']}_{i}", False)
            ]
            if flagged_unselected:
                if st.button(f":material/checklist: Select Flagged ({len(flagged_unselected)})", width="stretch", help="Check all words flagged by the audit"):
                    for i in flagged_unselected:
                        w = st.session_state.target_batch[i]
                        st.session_state[f"chk_swap_{w['id']}_{i}"] = True
                    st.rerun()
            elif num_selected > 0:
                if st.button(":material/close: Clear Selection", width="stretch", help="Uncheck all selected words"):
                    for i, w in enumerate(st.session_state.target_batch):
                        st.session_state[f"chk_swap_{w['id']}_{i}"] = False
                    st.rerun()

        cols = st.columns(4)
        for idx, word_item in enumerate(st.session_state.target_batch):
            col_target = cols[idx % 4]
            with col_target:
                pos = word_item["pos_type"]
                badge_class = "badge-noun" if pos == "Noun" else ("badge-verb" if pos == "Verb" else "badge-adj")
                word_text = word_item["word"]

                # Dynamic font sizing to prevent long words from displacing card layout
                w_len = len(word_text)
                if w_len >= 14:
                    font_size = "0.76rem"
                elif w_len >= 11:
                    font_size = "0.84rem"
                elif w_len >= 9:
                    font_size = "0.92rem"
                else:
                    font_size = "1.04rem"

                is_flagged = word_text.lower().strip() in flagged_dict
                flag_reason = flagged_dict.get(word_text.lower().strip(), "")
                is_checked = st.session_state.get(f"chk_swap_{word_item['id']}_{idx}", False)

                if is_checked:
                    if is_flagged:
                        card_style = (
                            "border: 2px solid #4F46E5; background: var(--studio-amber-bg); "
                            "box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.25);"
                        )
                    else:
                        card_style = (
                            "border: 2px solid #4F46E5; background: var(--studio-tint); "
                            "box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.15);"
                        )
                elif is_flagged:
                    card_style = (
                        "border: 2px solid #F59E0B; background: var(--studio-amber-bg); "
                        "box-shadow: 0 1px 4px rgba(245, 158, 11, 0.2);"
                    )
                else:
                    card_style = "border: 1px solid var(--studio-line); background: var(--studio-surface);"

                if is_flagged:
                    reason_html = (
                        f'<div style="margin-top: 6px; padding: 4px 6px; border-radius: 6px; '
                        f'background: var(--studio-amber-bg); border: 1px solid var(--studio-line); color: var(--studio-amber); '
                        f'font-size: 0.72rem; line-height: 1.25; font-weight: 550;">'
                        f'⚠️ <b>Mismatch:</b> {flag_reason}</div>'
                    )
                else:
                    reason_html = ""
                
                with st.container():
                    st.markdown(
                        f"""
                        <div class="word-card" style="{card_style} min-height: 54px; display: flex; flex-direction: column; justify-content: center; gap: 4px; box-sizing: border-box; padding: 10px 14px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; gap: 6px;">
                                <span style="color: var(--studio-ink) !important; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
                                    <strong style="color: var(--studio-ink) !important; font-size: {font_size}; letter-spacing: -0.01em;">{idx+1}. {word_text}</strong>
                                </span>
                                <span class="{badge_class}" style="margin: 0; flex-shrink: 0; font-size: 0.75rem; padding: 2px 7px;">{pos}</span>
                            </div>
                            {reason_html}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    col_chk, col_btn = st.columns([1.1, 1], vertical_alignment="center")
                    with col_chk:
                        st.checkbox(
                            "Select",
                            key=f"chk_swap_{word_item['id']}_{idx}",
                            help=f"Select '{word_text}' for batch swap"
                        )
                    with col_btn:
                        if st.button(f":material/refresh: Swap", key=f"swap_{word_item['id']}_{idx}", help=f"Swap '{word_item['word']}' instantly"):
                            selected_dom = st.session_state.get("selected_domain", "All Domains")
                            swapped = db.swap_single_word(pos, current_ids, domain=selected_dom)
                            if swapped:
                                st.session_state.pop(f"chk_swap_{word_item['id']}_{idx}", None)
                                updated_batch = list(st.session_state.target_batch)
                                updated_batch[idx] = swapped
                                set_target_batch(updated_batch, keep_direction=True, clear_lyrics=False)
                                st.session_state.master_prompt = ""
                                st.session_state.studio_suno_prompt = ""
                                st.session_state.graph_report = None
                                if st.session_state.get("word_fit_audit"):
                                    old_w = word_item["word"].lower().strip()
                                    cur_flagged = st.session_state.word_fit_audit.get("flagged_words", [])
                                    st.session_state.word_fit_audit["flagged_words"] = [
                                        fw for fw in cur_flagged if fw.get("word", "").lower().strip() != old_w
                                    ]
                                sync_active_session()
                                dom_info = f" [{swapped['domain']}]" if swapped.get("domain") and selected_dom != "All Domains" else ""
                                st.success(f"Swapped '{word_item['word']}' → '{swapped['word']}'{dom_info}. Re-run audit to verify!")
                                st.rerun()
                            else:
                                st.warning(f"No more unused {pos} words available to swap.")

        st.markdown("---")

        # Step 2: Gemini Mood & Style Analysis
        st.subheader(":material/auto_awesome: Step 2: Gemini Flash Mood & Musical Analysis")
        col_gem1, col_gem2 = st.columns([1.5, 2])
        
        with col_gem1:
            st.markdown("Analyze the 20 target words to get an emotional breakdown, genre, and structure.")
            if st.button(":material/auto_awesome: Run Gemini Analysis", type="secondary", width="stretch"):
                with st.spinner("Analyzing vocabulary mood with Gemini Flash..."):
                    res = gemini_client.analyze_vocabulary_mood(
                        current_words,
                        domain=st.session_state.selected_domain
                    )
                    st.session_state.mood_analysis = res
                    st.session_state.word_fit_audit = None
                    if res.get("genre"):
                        st.session_state.selected_genre = res["genre"]
                    if res.get("song_structure"):
                        st.session_state.selected_structure = res["song_structure"]
                    if res.get("creative_concept"):
                        st.session_state.custom_concept = res["creative_concept"]
                    sync_active_session()
                    st.rerun()

            if st.session_state.mood_analysis:
                analysis = st.session_state.mood_analysis
                st.success(f"Analyzed using: `{analysis.get('model_used', 'Gemini')}`")

        with col_gem2:
            if st.session_state.mood_analysis:
                analysis = st.session_state.mood_analysis
                mood_data = analysis.get("mood_breakdown", {})
                if mood_data:
                    mood_df = pd.DataFrame(list(mood_data.items()), columns=["Mood", "Percentage"])
                    mood_df = mood_df.sort_values(by="Percentage", ascending=False)
                    st.bar_chart(mood_df.set_index("Mood"), color="#4F46E5", height=220)

        # Style & Structure Selector
        st.markdown("#### 🎛️ Tune Musical Direction & Story Concept")
        tune_col1, tune_col2, tune_col3 = st.columns([1.5, 1, 1.5])
        with tune_col1:
            default_genre_idx = GENRES.index(st.session_state.selected_genre) if st.session_state.selected_genre in GENRES else 0
            new_genre = st.selectbox("Genre (Closed List)", GENRES, index=default_genre_idx)
            if new_genre != st.session_state.selected_genre:
                st.session_state.selected_genre = new_genre
                sync_active_session()

        with tune_col2:
            voc_options = ["Male", "Female", "Duet", "Instrumental"]
            default_voc_idx = voc_options.index(st.session_state.selected_vocalist) if st.session_state.selected_vocalist in voc_options else 0
            new_voc = st.selectbox("Lead Vocalist", voc_options, index=default_voc_idx)
            if new_voc != st.session_state.selected_vocalist:
                st.session_state.selected_vocalist = new_voc
                sync_active_session()

        with tune_col3:
            default_struct_idx = SONG_STRUCTURES.index(st.session_state.selected_structure) if st.session_state.selected_structure in SONG_STRUCTURES else 0
            new_struct = st.selectbox("Song Structure (Closed List)", SONG_STRUCTURES, index=default_struct_idx)
            if new_struct != st.session_state.selected_structure:
                st.session_state.selected_structure = new_struct
                sync_active_session()

        new_concept = st.text_area(
            ":material/lightbulb: Story / Creative Concept (Generated by Gemini, fully editable by you):",
            value=st.session_state.custom_concept,
            height=75,
            help="Tweak Gemini's concept or write your own practical everyday life scenario before generating the prompt."
        )
        if new_concept != st.session_state.custom_concept:
            st.session_state.custom_concept = new_concept
            sync_active_session()



        # Generate Prompts
        st.markdown("---")
        st.subheader(":material/content_copy: Step 3: Generation & Production Prompts")
        
        if st.button(":material/arrow_forward: Generate Final Prompt", type="primary", width="stretch"):
            mood_dict = st.session_state.mood_analysis.get("mood_breakdown", {}) if st.session_state.mood_analysis else {}
            concept = st.session_state.custom_concept.strip() or (
                st.session_state.mood_analysis.get("creative_concept", "") if st.session_state.mood_analysis else ""
            )
            
            with st.spinner("🚀 Crafting Master Songwriting Prompt, Suno Style, and Poster Art Prompt..."):
                used_content_words = db.get_previously_used_words(exclude_words=current_words)
                prompt_text = prompt_builder.generate_master_prompt(
                    target_words=current_words,
                    genre=st.session_state.selected_genre,
                    song_structure=st.session_state.selected_structure,
                    mood_analysis=mood_dict,
                    creative_concept=concept,
                    selected_domain=st.session_state.get("selected_domain", "All Domains"),
                    vocalist=st.session_state.selected_vocalist,
                    dialect="American English"
                )
                suno_text = prompt_builder.build_suno_style_prompt(
                    genre=st.session_state.selected_genre,
                    vocalist=st.session_state.selected_vocalist
                )
                poster_text = gemini_client.generate_studio_poster_prompt(
                    concept=concept,
                    genre=st.session_state.selected_genre,
                    vocalist=st.session_state.selected_vocalist,
                    title="[Song Title]"
                )
                st.session_state.master_prompt = prompt_text
                st.session_state.studio_suno_prompt = suno_text
                st.session_state.studio_poster_prompt = poster_text
                sync_active_session()

        if st.session_state.master_prompt:
            st.markdown("#### :material/music_note: 1. Suno AI Music Style Prompt (Ready to Paste into Suno):")
            st.caption("Dense, keyword-rich Suno style prompt (< 120 chars) tailored to your selected genre, tempo, and vocal clarity:")
            
            suno_prompt_val = st.session_state.studio_suno_prompt or prompt_builder.build_suno_style_prompt(
                genre=st.session_state.selected_genre,
                vocalist=st.session_state.selected_vocalist
            )
            suno_char_len = len(suno_prompt_val)
            suno_color = "#10B981" if suno_char_len <= 120 else "#EF4444"
            st.markdown(
                f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;'>"
                f"<small style='color: var(--studio-muted);'>📋 Click the copy icon in the box below to paste into Suno's 'Style of Music' box</small>"
                f"<small style='color: {suno_color}; font-weight: 700;'>Length: {suno_char_len} / 120 chars</small>"
                f"</div>",
                unsafe_allow_html=True
            )
            st.code(suno_prompt_val, language="markdown")

            st.markdown("<hr style='margin: 18px 0; border-color: var(--studio-line);'>", unsafe_allow_html=True)

            st.markdown("#### :material/palette: 2. Midjourney / DALL-E Album Cover Prompt (Poster Art):")
            st.caption("Artistic visual prompt capturing the genre aesthetic, lighting, and story atmosphere:")
            
            concept_for_poster = st.session_state.custom_concept.strip() or (
                st.session_state.mood_analysis.get("creative_concept", "") if st.session_state.mood_analysis else ""
            )
            poster_prompt_val = st.session_state.studio_poster_prompt or gemini_client.generate_studio_poster_prompt(
                concept=concept_for_poster,
                genre=st.session_state.selected_genre,
                vocalist=st.session_state.selected_vocalist,
                title="[Song Title]"
            )
            st.code(poster_prompt_val, language="markdown")

            st.markdown("<hr style='margin: 18px 0; border-color: var(--studio-line);'>", unsafe_allow_html=True)

            st.markdown("#### :material/edit_note: 3. Master Lyrics Prompt (Copy & Paste into Claude / GPT-4o):")
            st.caption("Full prompt containing all 20 target vocabulary words, real-world narrative concept, and strict Logic Gate:")
            st.code(st.session_state.master_prompt, language="markdown")

            st.markdown("<hr style='margin: 18px 0; border-color: var(--studio-line);'>", unsafe_allow_html=True)

            st.markdown("#### :material/fact_check: 4. Strict Song Audit Prompt (Ready to paste into Claude / ChatGPT):")
            st.caption("برومبت التدقيق النقدي الشامل لمراجعة الأغنية، المقاطع الصوتية، الطبيعية، وترابط القصة:")
            st.code(prompt_builder.build_song_audit_prompt(current_words), language="markdown")
    else:
        st.info("👉 Click **[Pull 20 Words]** above to select a batch of 20 unused words and begin.")
