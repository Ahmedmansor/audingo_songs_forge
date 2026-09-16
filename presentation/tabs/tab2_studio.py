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
)
from presentation.components.session import sync_active_session


def render_tab_studio():
    """Renders the Target Word Selection, Batch Management, and AI Prompt Generator."""
    st.subheader("🎯 Target Word Selection & AI Prompt Generator")

    # ─── Approved Session Drafts — Recovery Dropdown ───────────────────────────────────
    _all_drafts = db.list_studio_drafts()
    if _all_drafts:
        with st.expander("📂 Load from Approved Session Drafts (last 10)", expanded=False):
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
                if st.button("♻️ Load Draft (words only)", use_container_width=True, key="btn_load_draft_words"):
                    if _draft_batch:
                        st.session_state.target_batch = _draft_batch
                        st.session_state.mood_analysis = None
                        st.session_state.master_prompt = ""
                        st.session_state.studio_suno_prompt = ""
                        st.session_state.studio_poster_prompt = ""
                        st.session_state.custom_concept = ""
                        sync_active_session()
                        st.success("✅ Word batch restored from draft!")
                        st.rerun()
                    else:
                        st.warning("This draft has no words saved.")
            with _dc2:
                if st.button("📦 Load Draft (full session)", use_container_width=True, key="btn_load_draft_full"):
                    if _draft_payload:
                        st.session_state.target_batch = _draft_batch
                        st.session_state.mood_analysis = _draft_payload.get("mood_analysis", None)
                        st.session_state.master_prompt = _draft_payload.get("master_prompt", "")
                        st.session_state.studio_suno_prompt = _draft_payload.get("suno_prompt", "")
                        st.session_state.studio_poster_prompt = _draft_payload.get("poster_prompt", "")
                        st.session_state.custom_concept = _draft_payload.get("custom_concept", "")
                        st.session_state.selected_genre = _draft_payload.get("selected_genre", st.session_state.selected_genre)
                        st.session_state.selected_structure = _draft_payload.get("selected_structure", st.session_state.selected_structure)
                        st.session_state.selected_vocalist = _draft_payload.get("selected_vocalist", st.session_state.selected_vocalist)
                        sync_active_session()
                        st.success("✅ Full session restored from draft!")
                        st.rerun()
                    else:
                        st.warning("Could not load this draft.")
            with _dc3:
                if st.button("🗑️ Delete", use_container_width=True, key="btn_delete_draft"):
                    db.delete_studio_draft(_selected_draft_id)
                    st.success("Draft deleted.")
                    st.rerun()

    # ─── Domain Filter Selector ───────────────────────────────────────
    studio_dom_stats = db.get_domain_detailed_stats()
    total_uns_all = sum(d["unused"] for d in studio_dom_stats.values())
    all_dom_label = f"🌐 All Domains ({total_uns_all:,} Remaining - General Draw)"

    domain_options = [all_dom_label] + [
        f"{DOMAIN_CONFIG[d]['emoji']} {d} ({studio_dom_stats.get(d, {}).get('unused', 0):,} remaining / {studio_dom_stats.get(d, {}).get('total', 0):,})"
        for d in DOMAINS
    ]
    domain_key_map = {all_dom_label: "All Domains"}
    domain_label_from_key = {"All Domains": all_dom_label}
    for d in DOMAINS:
        lbl = f"{DOMAIN_CONFIG[d]['emoji']} {d} ({studio_dom_stats.get(d, {}).get('unused', 0):,} remaining / {studio_dom_stats.get(d, {}).get('total', 0):,})"
        domain_key_map[lbl] = d
        domain_label_from_key[d] = lbl

    current_selected_domain = st.session_state.get("selected_domain", "All Domains")
    default_domain_label = domain_label_from_key.get(current_selected_domain, all_dom_label)
    default_idx = domain_options.index(default_domain_label) if default_domain_label in domain_options else 0

    col_filter_ui, col_joker_toggle, col_filter_badge = st.columns([1.6, 1.1, 1.3], vertical_alignment="center")
    with col_filter_ui:
        chosen_domain_label = st.selectbox(
            "🎯 Filter by Vocabulary Domain:",
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
                '<div style="margin-top: 10px; font-size: 0.78rem; color: #94A3B8; font-style: italic;">'
                '🃏 الجوكر مدمج تلقائياً'
                '</div>',
                unsafe_allow_html=True
            )
            blend_joker = True
            st.session_state.blend_joker = True

    with col_filter_badge:
        if new_domain_val == "All Domains":
            badge_html = (
                f'<div style="margin-top: 12px; font-size: 0.82rem; color: #94A3B8; background: rgba(148,163,184,0.1); '
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
            if st.button("🎲 Random 20", type="secondary", use_container_width=True, help="Randomly pull 20 unused words (10 N, 6 V, 4 A) directly from SQLite."):
                active_domain = st.session_state.get("selected_domain", "All Domains")
                active_blend = st.session_state.get("blend_joker", True)
                new_batch = db.pull_20_words(domain=active_domain, blend_joker=active_blend)
                if len(new_batch) == 20:
                    st.session_state.target_batch = new_batch
                    st.session_state.mood_analysis = None
                    st.session_state.master_prompt = ""
                    st.session_state.studio_suno_prompt = ""
                    st.session_state.custom_concept = ""
                    sync_active_session()
                    if active_domain not in ("All Domains", "Basic / Neutral"):
                        mode_str = " (50% Domain + 50% Joker blend)" if active_blend else " (100% Pure Domain)"
                        dom_tag = f" from {active_domain}{mode_str}"
                    elif active_domain == "Basic / Neutral":
                        dom_tag = " from Basic / Neutral (Joker)"
                    else:
                        dom_tag = ""
                    st.success(f"Pulled 20 random unused words (10 Nouns, 6 Verbs, 4 Adjectives){dom_tag}!")
                    st.rerun()
                elif len(new_batch) > 0:
                    st.session_state.target_batch = new_batch
                    st.session_state.custom_concept = ""
                    st.session_state.studio_suno_prompt = ""
                    sync_active_session()
                    st.warning(f"Only {len(new_batch)} unused words available in database.")
                    st.rerun()
                else:
                    st.error("No unused words remaining in the database!")

        with b_col2:
            if st.button("🧠 Smart Thematic Pull", type="primary", use_container_width=True, help="Gemini analyzes 140 candidate unused words and selects 20 words (10 N, 6 V, 4 A) that share natural chemistry and relate to an authentic everyday life scenario."):
                active_domain = st.session_state.get("selected_domain", "All Domains")
                active_blend = st.session_state.get("blend_joker", True)
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
                        st.session_state.target_batch = curated_batch
                        st.session_state.mood_analysis = None
                        st.session_state.master_prompt = ""
                        st.session_state.studio_suno_prompt = ""
                        st.session_state.custom_concept = curation_res.get("theme_description", "")
                        sync_active_session()
                        theme_title = curation_res.get("theme_name", "Curated Storyline")
                        st.success(f"✨ Curated 20 thematic words for '{theme_title}' (10 Nouns, 6 Verbs, 4 Adjectives)!")
                        st.rerun()
                    elif len(curated_batch) > 0:
                        st.session_state.target_batch = curated_batch
                        st.session_state.custom_concept = curation_res.get("theme_description", "")
                        sync_active_session()
                        st.warning(f"Curated {len(curated_batch)} words.")
                        st.rerun()
                    else:
                        st.error("Could not curate a batch from unused words.")

        with b_col3:
            if st.button("🔄 Cancel & Redraw", use_container_width=True):
                active_domain = st.session_state.get("selected_domain", "All Domains")
                active_blend = st.session_state.get("blend_joker", True)
                new_batch = db.pull_20_words(domain=active_domain, blend_joker=active_blend)
                st.session_state.target_batch = new_batch
                st.session_state.mood_analysis = None
                st.session_state.master_prompt = ""
                st.session_state.studio_suno_prompt = ""
                st.session_state.custom_concept = ""
                sync_active_session()
                st.info("Batch redrawn.")
                st.rerun()

        with b_col4:
            if st.button("🧹 Clear", use_container_width=True, help="Clear active target batch"):
                st.session_state.target_batch = []
                st.session_state.mood_analysis = None
                st.session_state.master_prompt = ""
                st.session_state.studio_suno_prompt = ""
                st.session_state.custom_concept = ""
                db.clear_active_batch_state()
                st.rerun()

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
            other_pill = f'<span style="background: #F1F5F9; color: #475569; font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; border: 1px solid #CBD5E1;">⚪ {others_count} Other</span>' if others_count else ''
            st.markdown(
                f"""
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 2px;">
                    <span style="font-weight: 700; color: #0F172A; font-size: 1.05rem;">🎯 Active Target Batch:</span>
                    <span style="background: #EDE9FE; color: #5B21B6; font-size: 0.82rem; font-weight: 700; padding: 2px 9px; border-radius: 12px; border: 1px solid #DDD6FE;">{len(st.session_state.target_batch)} Words</span>
                    <span style="background: #E0E7FF; color: #3730A3; font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; border: 1px solid #C7D2FE;">🔵 {nouns_count} Nouns</span>
                    <span style="background: #DCFCE7; color: #166534; font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; border: 1px solid #BBF7D0;">🟢 {verbs_count} Verbs</span>
                    <span style="background: #FEF3C7; color: #92400E; font-size: 0.8rem; font-weight: 600; padding: 2px 8px; border-radius: 12px; border: 1px solid #FDE68A;">🟡 {adjs_count} Adjectives</span>
                    {other_pill}
                </div>
                """,
                unsafe_allow_html=True
            )
        with col_batch_actions:
            render_copy_words_toolbar(current_words)

        batch_domain_data = db.compute_domain_breakdown(current_words)
        render_domain_breakdown_section(batch_domain_data, title="📊 Active 20-Word Batch Domain Balance", compact=True)

        cols = st.columns(4)
        for idx, word_item in enumerate(st.session_state.target_batch):
            col_target = cols[idx % 4]
            with col_target:
                pos = word_item["pos_type"]
                badge_class = "badge-noun" if pos == "Noun" else ("badge-verb" if pos == "Verb" else "badge-adj")
                
                with st.container():
                    st.markdown(
                        f"""
                        <div class="word-card">
                            <span style="color: #0F172A !important;"><strong style="color: #0F172A !important; font-size: 1.05rem;">{idx+1}. {word_item['word']}</strong></span>
                            <span class="{badge_class}">{pos}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button(f"🔄 Swap", key=f"swap_{word_item['id']}_{idx}", help=f"Swap '{word_item['word']}' with another unused {pos}"):
                        swapped = db.swap_single_word(pos, current_ids)
                        if swapped:
                            st.session_state.target_batch[idx] = swapped
                            st.session_state.master_prompt = ""
                            st.session_state.studio_suno_prompt = ""
                            sync_active_session()
                            st.success(f"Swapped '{word_item['word']}' → '{swapped['word']}'")
                            st.rerun()
                        else:
                            st.warning(f"No more unused {pos} words available to swap.")

        st.markdown("---")

        # Step 2: Gemini Mood & Style Analysis
        st.subheader("🤖 Step 2: Gemini Flash Mood & Musical Analysis")
        col_gem1, col_gem2 = st.columns([1.5, 2])
        
        with col_gem1:
            st.markdown("Analyze the 20 target words to get an emotional breakdown, genre, and structure.")
            if st.button("✨ Run Gemini Analysis", type="secondary", use_container_width=True):
                with st.spinner("Analyzing vocabulary mood with Gemini Flash..."):
                    res = gemini_client.analyze_vocabulary_mood(current_words)
                    st.session_state.mood_analysis = res
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
            "💡 Story / Creative Concept (Generated by Gemini, fully editable by you):",
            value=st.session_state.custom_concept,
            height=75,
            help="Tweak Gemini's concept or write your own practical everyday life scenario before generating the prompt."
        )
        if new_concept != st.session_state.custom_concept:
            st.session_state.custom_concept = new_concept
            sync_active_session()

        # Generate Prompts
        st.markdown("---")
        st.subheader("📋 Step 3: Generation & Production Prompts")
        
        if st.button("🚀 Generate Final Prompt", type="primary", use_container_width=True):
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
                    previously_used_words=used_content_words
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
            st.markdown("#### 🎵 1. Suno AI Music Style Prompt (Ready to Paste into Suno):")
            st.caption("Dense, keyword-rich Suno style prompt (< 120 chars) tailored to your selected genre, tempo, and vocal clarity:")
            
            suno_prompt_val = st.session_state.studio_suno_prompt or prompt_builder.build_suno_style_prompt(
                genre=st.session_state.selected_genre,
                vocalist=st.session_state.selected_vocalist
            )
            suno_char_len = len(suno_prompt_val)
            suno_color = "#10B981" if suno_char_len <= 120 else "#EF4444"
            st.markdown(
                f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;'>"
                f"<small style='color: #94A3B8;'>📋 Click the copy icon in the box below to paste into Suno's 'Style of Music' box</small>"
                f"<small style='color: {suno_color}; font-weight: 700;'>Length: {suno_char_len} / 120 chars</small>"
                f"</div>",
                unsafe_allow_html=True
            )
            st.code(suno_prompt_val, language="markdown")

            st.markdown("<hr style='margin: 18px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

            st.markdown("#### 🎨 2. Midjourney / DALL-E Album Cover Prompt (Poster Art):")
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

            st.markdown("<hr style='margin: 18px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

            st.markdown("#### 📝 3. Master Lyrics Prompt (Copy & Paste into Claude / GPT-4o):")
            st.caption("Full prompt containing all 20 target vocabulary words, real-world narrative concept, and strict Logic Gate:")
            st.code(st.session_state.master_prompt, language="markdown")
    else:
        st.info("👉 Click **[Pull 20 Words]** above to select a batch of 20 unused words and begin.")
