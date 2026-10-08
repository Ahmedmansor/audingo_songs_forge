import streamlit as st
import time
import re
import html
import db
from scripts.lyrics_graph import run_refinement_graph, run_critic_only, compute_line_status
from domain.services.prompt_service import build_manual_surgical_prompt
from constants import get_category_profile

def render_tab_refinement():
    st.subheader("Find the right words.")
    st.markdown("<p class='sub-text'>Give your lyrics a thoughtful second pass. Refine the story, rhythm, and vocabulary.</p>", unsafe_allow_html=True)
    
    # Load persistence state if available
    persisted_state = db.load_refinement_state()
    initial_draft = persisted_state.get("draft_input", "")
    if not st.session_state.get("custom_concept") and persisted_state.get("concept"):
        st.session_state["custom_concept"] = persisted_state.get("concept")
    
    # Domain persistence: restore to refine_domain (separate from Studio's selected_domain)
    # Old drafts have no "domain", so persisted_state.get("domain") is None and we do NOT overwrite
    persisted_domain = persisted_state.get("domain")
    if persisted_domain and "refine_domain" not in st.session_state:
        st.session_state["refine_domain"] = persisted_domain

    active_domain = st.session_state.get("refine_domain") or st.session_state.get("selected_domain") or "Basic / Neutral"
    critic_profile = get_category_profile(active_domain)
    critic_name = critic_profile["critic_name"]
    
    # Bulletproof hydration: Get from session, fallback to DB
    current_report = st.session_state.get("graph_report")
    if not current_report:
        current_report = persisted_state.get("graph_report")
        if current_report:
            st.session_state["graph_report"] = current_report

    # Handle pending draft update BEFORE widget instantiation to prevent StreamlitWidgetAlreadyInstantiatedError
    if "pending_draft_update" in st.session_state:
        st.session_state["refine_draft"] = st.session_state.pop("pending_draft_update")
    elif "refine_draft" not in st.session_state:
        st.session_state["refine_draft"] = initial_draft

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("##### :material/input: Input")
        
        studio_domain = st.session_state.get("selected_domain")
        if studio_domain and active_domain != studio_domain:
            st.warning(f"⚠️ Critic category ({active_domain}) differs from Studio category ({studio_domain}).")
        
        col_meta1, col_meta2 = st.columns(2)
        with col_meta1:
            theme_val = st.text_input("Theme / Category (Synced)", value=active_domain, disabled=True, key="refine_theme")
            st.caption(f"🎭 **Active Critic:** {critic_name}")
        with col_meta2:
            genre_val = st.text_input("Genre & Style (Synced)", value=st.session_state.get("selected_genre", "Cinematic / Ballad"), disabled=True, key="refine_genre")
            
        concept_val = st.text_area(
            ":material/lightbulb: Story / Creative Concept (Synced from Studio):",
            value=st.session_state.get("custom_concept", ""),
            help="The critic will judge authenticity against this specific story.",
            key="refine_concept"
        )
        if concept_val:
            st.session_state["custom_concept"] = concept_val
        
        master_prompt_val = st.session_state.get("master_prompt", "")
        
        target_words_list = []
        if st.session_state.get("target_batch"):
            target_words_list = [w["word"] for w in st.session_state.target_batch]
        words_str = ", ".join(target_words_list) if target_words_list else ""
            
        if words_str:
            st.success(f"**Target Words ({len(target_words_list)}):** {words_str}")
        else:
            st.warning("⚠️ No target words active. Please select them in the Studio tab first.")
            
        draft = st.text_area(
            "Paste Initial Draft Lyrics Here", 
            height=300, 
            placeholder="[Verse 1]\nSitting in this diner...", 
            key="refine_draft"
        )

        critic_only_mode = st.toggle(
            "🔍 Critic only",
            value=st.session_state.get("critic_only_mode", True),
            key="critic_only_mode",
            help="وضع الناقد فقط: تدقيق ونقد الأسطر وحساب النسب والألوان فوراً بدون تعديل أو لوب. لا يغير حالة Refinement المحفوظة."
        )

        def _clean_draft_text(raw_text: str) -> str:
            lines = []
            for l in raw_text.splitlines():
                s = l.strip()
                s_lower = s.lower()
                if s_lower.startswith("[words used]") or s_lower.startswith("[words left out]"):
                    break
                if s_lower.startswith("[title]:") or s_lower.startswith("[genre]:") or s_lower.startswith("[suno style]:") or s_lower == "[lyrics]:":
                    continue
                lines.append(l)
            return "\n".join(lines).strip()
        
        if not critic_only_mode:
            if st.button("Start Refinement Pipeline", type="primary", width="stretch"):
                if draft.strip() and target_words_list:
                    draft_to_process = _clean_draft_text(draft)

                    with st.spinner("Initializing Multi-Agent Graph..."):
                        progress_container = st.empty()
                        
                        def ui_callback(msg):
                            progress_container.info(msg)
                            
                        start_time = time.time()
                        final_state = run_refinement_graph(
                            draft_to_process, 
                            target_words_list, 
                            theme_val, 
                            genre_val, 
                            concept_val, 
                            master_prompt_val,
                            dialect=st.session_state.get("selected_dialect", "American English"),
                            progress_callback=ui_callback
                        )
                        end_time = time.time()
                        
                        st.session_state["graph_report"] = final_state["final_report"]
                        st.session_state["graph_time"] = round(end_time - start_time, 1)
                        
                        # Persist state
                        db.save_refinement_state(draft, final_state["final_report"], concept_val, domain=active_domain)
                        st.rerun()
                else:
                    st.error("Please provide a draft and ensure target words are selected in the Studio.")
        else:
            if st.button("⚡ Run critic", type="primary", width="stretch", help="فحص وتقييم كل سطر بنسبة مئوية ولون بواسطة الناقد الصارم"):
                if draft.strip():
                    draft_to_process = _clean_draft_text(draft)

                    with st.spinner("Running Strict Critic..."):
                        start_time = time.time()
                        critic_report = run_critic_only(
                            draft=draft_to_process,
                            target_words=target_words_list,
                            theme=theme_val,
                            genre=genre_val,
                            concept=concept_val,
                            master_prompt=master_prompt_val,
                            dialect=st.session_state.get("selected_dialect", "American English")
                        )
                        st.session_state["critic_only_report"] = critic_report
                        st.session_state["critic_only_time"] = critic_report.get("time_taken", round(time.time() - start_time, 1))
                        st.rerun()
                else:
                    st.error("Please provide lyrics draft to critique.")
                
    with col2:
        if critic_only_mode:
            critic_report = st.session_state.get("critic_only_report")
            display_critic = (critic_report.get("critic_name") if critic_report else None) or critic_name
            st.markdown(f"##### :material/fact_check: {display_critic} Report")
            if critic_report:
                score = critic_report.get("overall_score", 0)
                m1, m2, m3 = st.columns(3)
                m1.metric("Authenticity Score", f"{score}%")
                m2.metric("Breakdown", f"🟢 {critic_report.get('passed_count', 0)} | 🟡 {critic_report.get('warn_count', 0)} | 🔴 {critic_report.get('flagged_count', 0)}")
                m3.metric("Time Taken", f"{critic_report.get('time_taken', 0)}s")

                st.info(f"🤖 **Model Active:** `{critic_report.get('model_used', 'Gemini')}` | 🎭 **Critic:** `{display_critic}`")

                # Manual surgical prompt copy button
                manual_prompt = build_manual_surgical_prompt(
                    lyrics_text=critic_report.get("raw_lyrics", ""),
                    line_breakdown=critic_report.get("line_breakdown", []),
                    theme=theme_val,
                    genre=genre_val,
                    concept=concept_val,
                    target_words=target_words_list,
                    selected_domain=active_domain
                )

                col_c1, col_c2 = st.columns([1.5, 1])
                with col_c1:
                    with st.popover(":material/content_copy: Copy manual refine prompt", width="stretch"):
                        st.markdown("**برومبت التعديل اليدوي الجراحي (External AI):**")
                        st.caption("اضغط أيقونة النسخ في الركن الأيمن للنسخ بضغطة زر وإرساله إلى Claude 3.5 Sonnet أو GPT-4o:")
                        st.code(manual_prompt, language="markdown")
                with col_c2:
                    if st.button(":material/refresh: إعادة التدقيق", width="stretch", help="مسح التقرير الحالي"):
                        st.session_state.pop("critic_only_report", None)
                        st.rerun()

                dropped = critic_report.get("dropped_words", [])
                if dropped:
                    st.warning(f"⚠️ **الناقد يوصي بإسقاط الكلمات التالية لعدم واقعيتها في السياق:** {', '.join(dropped)}")
            else:
                st.info("👈 ألصق كلمات الأغنية في الخانة على اليسار واضغط **Run critic** لتشغيل الناقد وفحص السطور بنسب مئوية وألوان فورية.")
        else:
            current_report = st.session_state.get("graph_report")
            pipeline_critic = (current_report.get("critic_name") if current_report else None) or critic_name
            st.markdown(f"##### :material/bar_chart: Final Report ({pipeline_critic})")

            if current_report:
                score = current_report.get("overall_score", 0)
                
                # Modern metric cards using Streamlit native columns
                m1, m2, m3 = st.columns(3)
                m1.metric("Authenticity Score", f"{score}%")
                m2.metric("Loops & API", f"{current_report.get('iterations_used', 0)} Loops / {current_report.get('total_requests', 0)} Reqs")
                m3.metric("Time Taken", f"{st.session_state.get('graph_time', 0)}s")
                
                # Show all models used in the process
                models_list = list(dict.fromkeys(current_report.get("models_used", ["Unknown"])))
                st.info(f"🤖 **Models Active:** `{'` | `'.join(models_list)}` | 🎭 **Critic:** `{pipeline_critic}`")
                
                with st.expander(":material/edit_note: Final Polished Lyrics", expanded=True):
                    lyrics_text = current_report.get("final_lyrics", "")
                    lyrics_html = f"""<div style="white-space: pre-wrap; font-family: 'Consolas', 'Courier New', monospace; background: var(--studio-bg); color: var(--studio-ink); padding: 18px; border-radius: 8px; font-size: 1.02rem; border: 1px solid var(--studio-line); line-height: 1.65; box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);">
{lyrics_text}
</div>"""
                    st.markdown(lyrics_html, unsafe_allow_html=True)
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(":material/input: نقل الكلمات تلقائياً للمسودة", width="stretch", help="ضغطة واحدة تنقل هذه الكلمات فوراً لخانة الإدخال على اليسار لبدء تحسين جديد"):
                            polished = lyrics_text
                            st.session_state["pending_draft_update"] = polished
                            db.save_refinement_state(polished, current_report, concept_val, domain=active_domain)
                            st.rerun()
                    with col_btn2:
                        if st.button(":material/arrow_forward: إرسال لمعمل الاعتماد (Commit Lab)", width="stretch", help="إرسال الكلمات المصقولة مباشرة إلى Tab 4 لحفظها واعتمادها"):
                            st.session_state["raw_lyrics_input"] = lyrics_text
                            st.toast("🚀 تم الإرسال إلى Commit Lab! افتح Tab 4 لحفظ الأغنية.")

                # External AI Surgical Prompt Exporter (Collapsed by default)
                with st.expander(":material/build: برومبت التعديل الخارجي (External AI Surgical Prompt)", expanded=False, key="ext_prompt_expander_closed"):
                    st.markdown("""<div style="font-size: 0.88rem; color: var(--studio-neutral-ink); margin-bottom: 12px; line-height: 1.5;">
خذ هذا البرومبت الجاهز وانسخه بضغطة زر إلى أي ذكاء اصطناعي خارجي (مثل <strong>Claude 3.5 Sonnet</strong> أو <strong>ChatGPT 4o</strong>). البرومبت مصمم جراحياً ليحتوي على الأسطر التي تحتاج تعديلاً فقط مع القواعد الصارمة لحماية الأسطر الخضراء.
</div>""", unsafe_allow_html=True)
                    
                    target_words_list_normal = []
                    if st.session_state.get("target_batch"):
                        target_words_list_normal = [w["word"] for w in st.session_state.target_batch]
                    elif current_report.get("words_kept"):
                        target_words_list_normal = current_report.get("words_kept", [])

                    external_prompt = build_manual_surgical_prompt(
                        lyrics_text=current_report.get("final_lyrics", ""),
                        line_breakdown=current_report.get("line_breakdown", []),
                        theme=theme_val,
                        genre=genre_val,
                        concept=concept_val,
                        target_words=target_words_list_normal,
                        selected_domain=active_domain
                    )
                    st.code(external_prompt, language="markdown")
                    
                with st.expander(":material/bar_chart: Word Integration Report", expanded=False):
                    kept = current_report.get("words_kept", [])
                    dropped = current_report.get("words_dropped", [])
                    
                    kept_html = "".join([f"<span style='background: rgba(16, 185, 129, 0.2); color: var(--studio-green); padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 700; margin: 0 6px 8px 0; display: inline-block; border: 1px solid #10B981; box-shadow: 0 1px 2px rgba(0,0,0,0.1);'>{w}</span>" for w in kept])
                    dropped_html = "".join([f"<span style='background: rgba(239, 68, 68, 0.2); color: var(--studio-red); padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 700; margin: 0 6px 8px 0; display: inline-block; border: 1px solid #EF4444; text-decoration: line-through; opacity: 0.85;'>{w}</span>" for w in dropped])
                    
                    display_kept = kept_html if kept_html else "<span style='color: var(--studio-muted); font-style: italic;'>None</span>"
                    st.markdown(f"<div style='margin-bottom: 15px;'><strong style='color: var(--studio-ink); font-size: 1.05rem;'>✅ Successfully Integrated ({len(kept)})</strong><div style='margin-top: 10px;'>{display_kept}</div></div>", unsafe_allow_html=True)
                    
                    if dropped:
                        st.markdown(f"<div><strong style='color: var(--studio-ink); font-size: 1.05rem;'>❌ Dropped by Critic ({len(dropped)})</strong><div style='margin-top: 10px;'>{dropped_html}</div></div>", unsafe_allow_html=True)

                with st.expander(f"📜 API Requests & Execution Log ({current_report.get('total_requests', 9)} Requests)", expanded=False):
                    exec_log = current_report.get("execution_log")
                    if not exec_log:
                        iterations = current_report.get("iterations_used", 5)
                        models = current_report.get("models_used", ["gemini-3.6-flash"])
                        total_reqs = current_report.get("total_requests", 9)
                        
                        exec_log = []
                        req_counter = 1
                        for loop_i in range(1, iterations + 1):
                            m_critic = models[(req_counter - 1) % len(models)]
                            exec_log.append({
                                "request_num": req_counter,
                                "loop": loop_i,
                                "agent": "Critic Agent (الناقد اللغوي)",
                                "model": m_critic,
                                "action": f"فحص الأصالة وتعيين درجات الأسطر (تقييم الدورة {loop_i})"
                            })
                            req_counter += 1
                            
                            if req_counter <= total_reqs:
                                m_editor = models[(req_counter - 1) % len(models)]
                                exec_log.append({
                                    "request_num": req_counter,
                                    "loop": loop_i,
                                    "agent": "Editor Agent (المحرر الفني)",
                                    "model": m_editor,
                                    "action": "إعادة صياغة العيوب وضبط تدفق القوافي والأوزان"
                                })
                                req_counter += 1

                    log_html = "<div style='display: flex; flex-direction: column; gap: 8px; margin-top: 5px;'>"
                    for item in exec_log:
                        r_num = item.get("request_num", 0)
                        r_loop = item.get("loop", 0)
                        r_agent = item.get("agent", "")
                        r_model = item.get("model", "")
                        r_action = item.get("action", "")
                        border_color = "#10B981" if "Critic" in r_agent else "#6366F1"
                        
                        log_html += f"""<div style="background: var(--studio-bg); border: 1px solid var(--studio-line); border-left: 3px solid {border_color}; border-radius: 6px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; gap: 10px;">
        <div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="background: var(--studio-line); color: var(--studio-ink); padding: 2px 7px; border-radius: 4px; font-size: 0.75rem; font-weight: 700;">Req #{r_num}</span>
                <span style="color: var(--studio-muted); font-size: 0.8rem;">Loop {r_loop}</span>
                <strong style="color: var(--studio-ink); font-size: 0.9rem;">{r_agent}</strong>
            </div>
            <div style="color: var(--studio-neutral-ink); font-size: 0.85rem; margin-top: 4px;">{r_action}</div>
        </div>
        <div style="flex-shrink: 0;">
            <span style="background: rgba(59, 130, 246, 0.15); color: var(--studio-blue); padding: 3px 8px; border-radius: 12px; font-size: 0.75rem; font-family: monospace; border: 1px solid rgba(59, 130, 246, 0.3);">{r_model}</span>
        </div>
    </div>"""
                    log_html += "</div>"
                    st.markdown(log_html, unsafe_allow_html=True)
            else:
                st.info("👈 Enter your draft lyrics and click **Start Refinement Pipeline** to run the multi-agent critique and optimization.")

    # Full-width Line-by-Line Section
    if critic_only_mode:
        critic_report = st.session_state.get("critic_only_report")
        if critic_report:
            lines = critic_report.get("line_breakdown", [])
            if lines:
                st.divider()
                total_lines = len(lines)
                passed_lines = critic_report.get("passed_count", 0)
                warn_lines = critic_report.get("warn_count", 0)
                flagged_lines = critic_report.get("flagged_count", 0)

                # Export text
                breakdown_lines_export = [
                    f"# 🔍 CRITIC EVALUATION (Score: {critic_report.get('overall_score', 0)}% | Total: {total_lines} | 🟢 {passed_lines} | 🟡 {warn_lines} | 🔴 {flagged_lines})",
                    f"- Theme: {theme_val} | Genre: {genre_val}",
                    f"- Story: {concept_val}\n",
                    "## 📜 Line-by-Line Scores & Feedback:"
                ]
                for idx, line_data in enumerate(lines, 1):
                    s_col = line_data.get("color", "⚪")
                    l_txt = line_data.get("line", "")
                    l_sc = line_data.get("score", 0)
                    l_cm = line_data.get("comment") or line_data.get("issue", "")
                    breakdown_lines_export.append(f'{idx}. [{s_col} {l_sc}%] "{l_txt}"\n   ↳ Note: {l_cm}')
                full_breakdown_text = "\n".join(breakdown_lines_export)

                col_title, col_copy = st.columns([3.2, 1.3])
                with col_title:
                    header_html = f"""<div style="margin-top: 10px; margin-bottom: 8px;">
<h3 style="margin: 0; color: var(--studio-ink); font-size: 1.35rem; font-weight: 700; letter-spacing: -0.02em;">
🔍 جدول نقد وتدقيق السطور (Critic Only Breakdown)
</h3>
<p style="margin: 4px 0 10px 0; color: var(--studio-muted); font-size: 0.92rem;">
تقييم كل سطر بنسبة مئوية ولون بناءً على المعايير الصارمة: 🟢 ≥ 90 | 🟡 75-89 | 🔴 &lt; 75
</p>
<div style="display: flex; gap: 8px; flex-wrap: wrap;">
<span style="background: var(--studio-line); color: var(--studio-neutral-ink); padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; border: 1px solid var(--studio-line);">
Total: {total_lines} Lines
</span>
<span style="background: rgba(16, 185, 129, 0.15); color: var(--studio-green); padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; border: 1px solid rgba(16, 185, 129, 0.3);">
🟢 {passed_lines} Passed (≥ 90%)
</span>
<span style="background: rgba(245, 158, 11, 0.15); color: var(--studio-amber); padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; border: 1px solid rgba(245, 158, 11, 0.3);">
🟡 {warn_lines} Polished (75-89%)
</span>
<span style="background: rgba(239, 68, 68, 0.15); color: var(--studio-red); padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; border: 1px solid rgba(239, 68, 68, 0.3);">
🔴 {flagged_lines} Flagged (&lt; 75%)
</span>
</div>
</div>"""
                    st.markdown(header_html, unsafe_allow_html=True)
                with col_copy:
                    st.write("")
                    with st.popover(":material/content_copy: نسخ تفاصيل التقييم", width="stretch"):
                        st.markdown("**تقرير السطور والتقييمات:**")
                        st.caption("اضغط زر النسخ في أعلى اليمين لنسخ التقرير بالكامل:")
                        st.code(full_breakdown_text, language="markdown")

                # Build table rows
                table_rows = []
                for item in lines:
                    idx = item.get("number", 0)
                    line_txt = html.escape(item.get("line", ""))
                    score_val = item.get("score", 0)
                    color_val = item.get("color", "⚪")
                    reason_txt = html.escape(item.get("comment") or item.get("issue") or "none")

                    if score_val >= 90:
                        row_border = "#10B981"
                        badge_bg = "rgba(16, 185, 129, 0.12)"
                        badge_text = "var(--studio-green)"
                        badge_border = "#34D399"
                    elif score_val >= 75:
                        row_border = "#F59E0B"
                        badge_bg = "rgba(245, 158, 11, 0.12)"
                        badge_text = "var(--studio-amber)"
                        badge_border = "#FBBF24"
                    else:
                        row_border = "#EF4444"
                        badge_bg = "rgba(239, 68, 68, 0.12)"
                        badge_text = "var(--studio-red)"
                        badge_border = "#F87171"

                    table_rows.append(f"""
<tr style="border-bottom: 1px solid #E5E5EA;">
    <td style="padding: 12px 14px; font-weight: 700; color: var(--studio-muted); border-left: 4px solid {row_border}; width: 45px; text-align: center;">{idx}</td>
    <td style="padding: 12px 14px; font-weight: 600; color: var(--studio-ink); font-size: 0.98rem; line-height: 1.45;">{line_txt}</td>
    <td style="padding: 12px 14px; font-weight: 800; font-size: 0.95rem; text-align: center; width: 85px;">
        <span style="background: {badge_bg}; color: {badge_text}; padding: 3px 10px; border-radius: 12px; border: 1px solid {badge_border};">{score_val}%</span>
    </td>
    <td style="padding: 12px 14px; text-align: center; font-size: 1.2rem; width: 60px;">{color_val}</td>
    <td style="padding: 12px 14px; color: {badge_text}; font-size: 0.9rem; line-height: 1.4; font-style: italic;">{reason_txt}</td>
</tr>
""")

                table_html = f"""<div style="border: 1px solid var(--studio-line); border-radius: 10px; overflow: hidden; background: var(--studio-surface); box-shadow: 0 1px 3px rgba(0,0,0,0.04); margin-top: 14px; margin-bottom: 24px;">
<table style="width: 100%; border-collapse: collapse; text-align: left; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <thead>
        <tr style="background: var(--studio-bg); border-bottom: 1px solid var(--studio-line);">
            <th style="padding: 11px 14px; font-size: 0.82rem; font-weight: 700; color: var(--studio-muted); text-align: center; width: 45px;">#</th>
            <th style="padding: 11px 14px; font-size: 0.82rem; font-weight: 700; color: var(--studio-muted);">السطر (Lyric Line)</th>
            <th style="padding: 11px 14px; font-size: 0.82rem; font-weight: 700; color: var(--studio-muted); text-align: center; width: 85px;">النسبة</th>
            <th style="padding: 11px 14px; font-size: 0.82rem; font-weight: 700; color: var(--studio-muted); text-align: center; width: 60px;">اللون</th>
            <th style="padding: 11px 14px; font-size: 0.82rem; font-weight: 700; color: var(--studio-muted);">السبب / الملاحظة (Reason & Deductions)</th>
        </tr>
    </thead>
    <tbody>
        {''.join(table_rows)}
    </tbody>
</table>
</div>"""
                st.markdown(table_html, unsafe_allow_html=True)
    elif current_report:
        lines = current_report.get("line_breakdown", [])
        if lines:
            st.divider()
            
            # Quick summary metrics for the breakdown
            total_lines = len(lines)
            passed_lines = sum(1 for l in lines if l.get("status") == "✅" or l.get("score", 0) >= 90)
            warn_lines = sum(1 for l in lines if (75 <= l.get("score", 0) < 90) or l.get("status") == "⚠️")
            flagged_lines = sum(1 for l in lines if l.get("score", 0) < 75 or l.get("status") in ["❌", "🗑️"])
            
            # Prepare full copyable breakdown text for external AI
            breakdown_lines_export = [
                f"# 🔍 CRITIC EVALUATION BREAKDOWN (Total: {total_lines} | ✅ {passed_lines} | ⚠️ {warn_lines} | ❌ {flagged_lines})",
                f"- Theme: {theme_val} | Genre: {genre_val}",
                f"- Story: {concept_val}\n",
                "## 📜 Line-by-Line Scores & Feedback:"
            ]
            for idx, line_data in enumerate(lines, 1):
                s_icon = line_data.get("status", "❓")
                l_txt = line_data.get("line", "")
                l_sc = line_data.get("score", 0)
                l_cm = line_data.get("comment", "")
                breakdown_lines_export.append(f'{idx}. [{s_icon} {l_sc}%] "{l_txt}"\n   ↳ Note: {l_cm}')
            
            full_breakdown_text = "\n".join(breakdown_lines_export)

            if flagged_lines > 0:
                flagged_badge = f'<span style="background: rgba(239, 68, 68, 0.15); color: var(--studio-red); padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; border: 1px solid rgba(239, 68, 68, 0.3);">❌ {flagged_lines} Flagged</span>'
            else:
                flagged_badge = '<span style="background: rgba(16, 185, 129, 0.12); color: var(--studio-green); padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; border: 1px solid rgba(16, 185, 129, 0.25);">✨ 0 Flagged (Clean!)</span>'

            warn_badge = f'<span style="background: rgba(245, 158, 11, 0.15); color: var(--studio-amber); padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; border: 1px solid rgba(245, 158, 11, 0.3);">⚠️ {warn_lines} Polished</span>' if warn_lines else ''

            col_title, col_copy = st.columns([3.2, 1.3])
            with col_title:
                header_html = f"""<div style="margin-top: 10px; margin-bottom: 8px;">
<h3 style="margin: 0; color: var(--studio-ink); font-size: 1.35rem; font-weight: 700; letter-spacing: -0.02em;">
🔍 Critic's Line-by-Line Breakdown
</h3>
<p style="margin: 4px 0 10px 0; color: var(--studio-muted); font-size: 0.92rem;">
Full evaluation of every lyric line scored for authenticity, natural delivery, and story coherence.
</p>
<div style="display: flex; gap: 8px; flex-wrap: wrap;">
<span style="background: var(--studio-line); color: var(--studio-neutral-ink); padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; border: 1px solid var(--studio-line);">
Total: {total_lines} Lines
</span>
<span style="background: rgba(16, 185, 129, 0.15); color: var(--studio-green); padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; border: 1px solid rgba(16, 185, 129, 0.3);">
✅ {passed_lines} Passed
</span>
{warn_badge}
{flagged_badge}
</div>
</div>"""
                st.markdown(header_html, unsafe_allow_html=True)
            with col_copy:
                st.write("")
                with st.popover(":material/content_copy: نسخ التقرير بالتفاصيل", width="stretch"):
                    st.markdown("**تقرير التقييم الشامل (السطور + السكور + التعليقات):**")
                    st.caption("اضغط أيقونة النسخ في الركن الأيمن لنسخ التقرير بالكامل وإرساله للذكاء الاصطناعي الخارجي:")
                    st.code(full_breakdown_text, language="markdown")
            
            grid_html = "<div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 440px), 1fr)); gap: 14px; width: 100%; margin-bottom: 30px;'>"
            for line_data in lines:
                l_score = line_data.get("score", 0)
                status = line_data.get("status", "❓")
                text = line_data.get("line", "")
                comment = line_data.get("comment", "")
                
                if l_score >= 90 or status == "✅":
                    card_bg = "linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, var(--studio-bg) 100%)"
                    border_color = "#10B981"
                    badge_bg = "var(--studio-surface)"
                    badge_text_color = "#047857"
                    badge_border = "#34D399"
                    feedback_color = "var(--studio-green)"
                    icon = "✅"
                elif l_score < 75 or status in ["❌", "🗑️"]:
                    card_bg = "linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, var(--studio-bg) 100%)"
                    border_color = "#EF4444"
                    badge_bg = "var(--studio-surface)"
                    badge_text_color = "#B91C1C"
                    badge_border = "#F87171"
                    feedback_color = "var(--studio-red)"
                    icon = "❌"
                else:
                    card_bg = "linear-gradient(135deg, rgba(245, 158, 11, 0.12) 0%, var(--studio-bg) 100%)"
                    border_color = "#F59E0B"
                    badge_bg = "var(--studio-surface)"
                    badge_text_color = "#B45309"
                    badge_border = "#FBBF24"
                    feedback_color = "var(--studio-amber)"
                    icon = "⚠️"

                card_html = f"""<div style="background: {card_bg}; border-left: 4px solid {border_color}; border-top: 1px solid var(--studio-line); border-right: 1px solid var(--studio-line); border-bottom: 1px solid var(--studio-line); border-radius: 8px; padding: 14px 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); display: flex; flex-direction: column; justify-content: space-between; gap: 8px;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 14px;">
        <span style="font-size: 1.05rem; font-weight: 600; color: var(--studio-ink); line-height: 1.45; word-break: break-word;">{text}</span>
        <div style="background: {badge_bg}; color: {badge_text_color}; padding: 3px 10px; border-radius: 20px; border: 1.5px solid {badge_border}; font-size: 0.85rem; font-weight: 800; display: inline-flex; align-items: center; gap: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.15); flex-shrink: 0;">
            <span>{icon}</span> <span>{l_score}%</span>
        </div>
    </div>
    <div style="font-size: 0.92rem; color: {feedback_color}; font-style: italic; line-height: 1.5; padding-top: 2px;">
        "{comment}"
    </div>
</div>"""
                grid_html += card_html
            grid_html += "</div>"
            st.markdown(grid_html, unsafe_allow_html=True)


