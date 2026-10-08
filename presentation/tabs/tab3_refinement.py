import streamlit as st
import time
import re
import db
from scripts.lyrics_graph import run_refinement_graph

def render_tab_refinement():
    st.subheader("✨ Step 4: AI Lyrics Refinement Graph (Pro Max)")
    st.markdown("<p class='sub-text'>Refine, validate, and perfect the drafted lyrics using a multi-agent AI pipeline.</p>", unsafe_allow_html=True)
    
    # Load persistence state if available
    persisted_state = db.load_refinement_state()
    initial_draft = persisted_state.get("draft_input", "")
    if not st.session_state.get("custom_concept") and persisted_state.get("concept"):
        st.session_state["custom_concept"] = persisted_state.get("concept")
    
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
        st.markdown("##### 📥 Input")
        
        col_meta1, col_meta2 = st.columns(2)
        with col_meta1:
            theme_val = st.text_input("Theme / Category (Synced)", value=st.session_state.get("selected_domain", "Street & Daily Life"), disabled=True, key="refine_theme")
        with col_meta2:
            genre_val = st.text_input("Genre & Style (Synced)", value=st.session_state.get("selected_genre", "Cinematic / Ballad"), disabled=True, key="refine_genre")
            
        concept_val = st.text_area(
            "💡 Story / Creative Concept (Synced from Studio):",
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
        
        if st.button("Start Refinement Pipeline", type="primary", use_container_width=True):
            if draft.strip() and target_words_list:
                # Clean up metadata sections if the user accidentally pasted them
                clean_draft = []
                for line in draft.splitlines():
                    if line.strip().lower().startswith("[words used]") or line.strip().lower().startswith("[words left out]"):
                        break
                    clean_draft.append(line)
                draft_to_process = "\n".join(clean_draft).strip()

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
                        progress_callback=ui_callback
                    )
                    end_time = time.time()
                    
                    st.session_state["graph_report"] = final_state["final_report"]
                    st.session_state["graph_time"] = round(end_time - start_time, 1)
                    
                    # Persist state
                    db.save_refinement_state(draft, final_state["final_report"], concept_val)
                    st.rerun()
            else:
                st.error("Please provide a draft and ensure target words are selected in the Studio.")
                
    with col2:
        st.markdown("##### 📊 Final Report")
        current_report = st.session_state.get("graph_report")

        if current_report:
            score = current_report.get("overall_score", 0)
            
            # Modern metric cards using Streamlit native columns
            m1, m2, m3 = st.columns(3)
            m1.metric("Authenticity Score", f"{score}%")
            m2.metric("Loops & API", f"{current_report.get('iterations_used', 0)} Loops / {current_report.get('total_requests', 0)} Reqs")
            m3.metric("Time Taken", f"{st.session_state.get('graph_time', 0)}s")
            
            # Show all models used in the process
            models_list = list(dict.fromkeys(current_report.get("models_used", ["Unknown"])))
            st.info(f"🤖 **Models Active:** `{'` | `'.join(models_list)}`")
            
            with st.expander("📝 Final Polished Lyrics", expanded=True):
                lyrics_text = current_report.get("final_lyrics", "")
                lyrics_html = f"""<div style="white-space: pre-wrap; font-family: 'Consolas', 'Courier New', monospace; background: #0F172A; color: #F8FAFC; padding: 18px; border-radius: 8px; font-size: 1.02rem; border: 1px solid #334155; line-height: 1.65; box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);">
{lyrics_text}
</div>"""
                st.markdown(lyrics_html, unsafe_allow_html=True)
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("📥 نقل الكلمات تلقائياً للمسودة", use_container_width=True, help="ضغطة واحدة تنقل هذه الكلمات فوراً لخانة الإدخال على اليسار لبدء تحسين جديد"):
                        polished = lyrics_text
                        st.session_state["pending_draft_update"] = polished
                        db.save_refinement_state(polished, current_report, concept_val)
                        st.rerun()
                with col_btn2:
                    if st.button("🚀 إرسال لمعمل الاعتماد (Commit Lab)", use_container_width=True, help="إرسال الكلمات المصقولة مباشرة إلى Tab 4 لحفظها واعتمادها"):
                        st.session_state["raw_lyrics_input"] = lyrics_text
                        st.toast("🚀 تم الإرسال إلى Commit Lab! افتح Tab 4 لحفظ الأغنية.")

            # External AI Surgical Prompt Exporter (Collapsed by default)
            with st.expander("🛠️ برومبت التعديل الخارجي (External AI Surgical Prompt)", expanded=False, key="ext_prompt_expander_closed"):
                st.markdown("""<div style="font-size: 0.88rem; color: #CBD5E1; margin-bottom: 12px; line-height: 1.5;">
خذ هذا البرومبت الجاهز وانسخه بضغطة زر إلى أي ذكاء اصطناعي خارجي (مثل <strong>Claude 3.5 Sonnet</strong> أو <strong>ChatGPT 4o</strong>). البرومبت مصمم جراحياً ليحتوي على الأسطر التي تحتاج تعديلاً فقط مع القواعد الصارمة لحماية الأسطر الخضراء.
</div>""", unsafe_allow_html=True)
                
                theme_val = st.session_state.get("selected_domain", "Street & Daily Life")
                genre_val = st.session_state.get("selected_genre", "Cinematic / Ballad")
                concept_val = st.session_state.get("refine_concept") or st.session_state.get("custom_concept", "")
                if not concept_val.strip():
                    concept_val = "A relatable everyday story grounded in real human conversation and situations."
                
                # Normalize dialect in story text
                concept_val = re.sub(r"\bmates\b", "friends", concept_val, flags=re.I)
                concept_val = re.sub(r"\bmate\b", "friend", concept_val, flags=re.I)
                
                # Fetch target words list from session state or current report
                target_words_list = []
                if st.session_state.get("target_batch"):
                    target_words_list = [w["word"] for w in st.session_state.target_batch]
                elif current_report.get("words_kept"):
                    target_words_list = current_report.get("words_kept", [])
                words_joined = ", ".join(target_words_list) if target_words_list else "None specified"
                
                lines_breakdown = current_report.get("line_breakdown", [])
                
                # Strict Green lock rule: score must be >= 90 AND status must be ✅
                passed_lines = [l for l in lines_breakdown if l.get("status") == "✅" and l.get("score", 0) >= 90]
                critical_lines = [l for l in lines_breakdown if l.get("status") in ["❌", "🗑️"] or l.get("score", 0) < 70]
                warning_lines = [l for l in lines_breakdown if (l.get("status") == "⚠️") or (l.get("status") == "✅" and l.get("score", 0) < 90)]
                
                crit_text = "\n".join([f'- Line: "{l.get("line", "")}"\n  Score: {l.get("score", 0)}%\n  Critique: {l.get("comment", "")}' for l in critical_lines]) if critical_lines else "None (All lines passed critical checks!)"
                warn_text = "\n".join([f'- Line: "{l.get("line", "")}"\n  Score: {l.get("score", 0)}%\n  Critique: {l.get("comment", "")}' for l in warning_lines]) if warning_lines else "None"
                passed_text = "\n".join([f'- "{l.get("line", "")}"' for l in passed_lines]) if passed_lines else "None"
                
                # Build explicitly tagged lyrics where each line tells the external AI its exact status
                status_dict = {}
                for l in lines_breakdown:
                    raw_txt = l.get("line", "").strip().lower()
                    score = l.get("score", 0)
                    st_val = l.get("status", "✅")
                    if st_val in ["❌", "🗑️"] or score < 70:
                        eff_status = "❌"
                    elif st_val == "⚠️" or score < 90:
                        eff_status = "⚠️"
                    else:
                        eff_status = "✅"
                    if raw_txt:
                        status_dict[raw_txt] = eff_status
                
                annotated_lines = []
                for raw_l in lyrics_text.splitlines():
                    cleaned = raw_l.strip().lower().strip(",").strip(".")
                    if not raw_l.strip() or raw_l.strip().startswith("["):
                        annotated_lines.append(raw_l)
                    else:
                        match_status = None
                        for k, line_status in status_dict.items():
                            if k in cleaned or cleaned in k:
                                match_status = line_status
                                break
                        if match_status == "❌":
                            annotated_lines.append(f"[🚨 REWRITE REQUIRED ❌] {raw_l}")
                        elif match_status == "⚠️":
                            annotated_lines.append(f"[⚠️ OPTIONAL POLISH] {raw_l}")
                        elif match_status == "✅":
                            annotated_lines.append(f"[🔒 LOCKED ✅ - DO NOT TOUCH] {raw_l}")
                        else:
                            annotated_lines.append(f"[⚠️ OPTIONAL POLISH] {raw_l}")
                annotated_lyrics_block = "\n".join(annotated_lines)
                
                external_prompt = f"""You are an expert English linguist and a professional ESL teacher who edits song lyrics for learners.
Your mission is to perform SURGICAL REPAIRS on the song lyrics below.

THE GOAL: the learner should be able to memorize ANY single line and use it as-is in real life. Every line must be a natural sentence a native speaker would actually say, and it must make sense when read alone.

CRITICAL PEDAGOGICAL MISSION:
This song is an educational song built around a strict list of target vocabulary words.
Every target word that is currently in the lyrics MUST be preserved. Do not add target words that are missing. Dropping or replacing a present target word with a synonym is a critical failure.

CONTEXTUAL ANCHORS:
- Theme: "{theme_val}"
- Musical Genre: "{genre_val}"
- Core Story / Setting / Concept: "{concept_val}"
- Dialect: American English (never mix dialects; replace British-only words like "mate" unless they are protected target words in a locked line)

🎯 TARGET VOCABULARY (Preserve every target word currently in the lyrics; do not add missing ones):
{words_joined}

🔒 VERIFIED GREEN LINES ({len(passed_lines)} Lines - 100% LOCKED, DO NOT CHANGE):
{passed_text}

🚨 CRITICAL FLAWED LINES (Must be rewritten - Status ❌):
{crit_text}

⚠️ MINOR WARNING LINES (Only tweak if it improves flow - Status ⚠️):
{warn_text}

---
CURRENT ANNOTATED SONG LYRICS (Follow the tags next to each line):
{annotated_lyrics_block}
---

=== SURGICAL REPAIR INSTRUCTIONS (OVERRIDE ANY CONFLICT ABOVE) ===

A. GREEN LINES (🔒) ARE LOCKED IN THE LYRICS OUTPUT.
   Never delete, reorder, merge, split, or reword them in Part 1. Treat them as fixed anchors. Every green line must appear in the output exactly once per place it appears now, in the same position.

B. EDIT SCOPE: Edit ONLY the ⚠️ (yellow) and ❌ (red) lines. If none are red, do not invent problems. A yellow line may be kept unchanged if no real improvement exists.

C. TARGET WORDS & TONE:
   - Every target word currently in the lyrics must remain intact. Do not add target words that are missing.
   - Do NOT replace any present target word with a synonym.
   - Do NOT add new profanity or crude vulgarities in edited lines. Existing coarse language inside green lines is intentional (street-life realism) and must not be treated as an error.

D. IMPROVEMENT GOALS FOR EDITED LINES (priority order):
   1. THEMATIC CONSISTENCY & SETTING CONTINUITY: Every edited line must stay inside the song's theme ("{theme_val}") and established setting / story ("{concept_val}"). Do not introduce new locations, characters, or topics that drift away from the central story. If a line does not serve the core story, rewrite it.
   2. PRACTICAL USABILITY:
      - An ESL learner who memorizes the line should be able to say it naturally in real life. Prefer everyday spoken English over poetic or literary phrasing.
      - Use natural contractions (I'm, don't, can't); avoid stiff forms.
      - Standalone test: read alone, the line must be natural and useful.
   3. NO FORCED RHYME: A line must add real narrative meaning, not exist only to rhyme.
   4. NO REPETITION: Avoid repeating the same opening word or key noun in nearby lines.
   5. FLOW & MELODY: Keep syllable count (±1) and rhyme scheme so the melody still fits.
   6. LENGTH: 6 to 9 syllables per edited line (±1).

E. FINAL SELF-CHECK (execute silently before outputting):
   - Count green lines: none missing, none changed, none repositioned.
   - Verify all present target words are still preserved.
   - Ensure each edited line passes goals 1 to 6 (including Standalone test and 6-9 syllables).
   - If a yellow line cannot be improved, keep it as is.

F. OUTPUT FORMAT:
   Part 1: The complete clean lyrics (without any [🔒], [🚨], or [⚠️] tags), ready to paste.
   Part 2: Change log, one line per edited line:
   "Original line" → "New line" | Reason for change
   (If nothing was edited, write "No edits needed".)
   
   === REVIEW ===
   Part 3: GREEN LINE REVIEW (suggestions only, NOT applied to Part 1).
   Check the green lines against goals D1 to D6, plus:
   - Flag any green line that breaks thematic consistency or setting continuity.
   - Is the line natural spoken English a learner can reuse in daily life?
   - Is the register (rude, formal, poetic, profane) flagged for the learner?
   - Is there weak coherence, forced rhyme, or repetition across the whole song?
   - Does any green line clash with an edit made in Part 1?
   Only mention a green line if you have a REAL, specific improvement. Do not pad the list. For each one give:
   "Original → Suggested | reason | priority (high / medium / low)"
   If nothing is worth changing, write "Green lines are solid, no suggestions."
   Finish with a verdict: overall coherence, educational value, and whether the song is ready to publish.

G. NEVER apply Part 3 suggestions to Part 1 unless the user explicitly approves them in the next message."""
                
                st.code(external_prompt, language="markdown")
                
            with st.expander("📊 Word Integration Report", expanded=False):
                kept = current_report.get("words_kept", [])
                dropped = current_report.get("words_dropped", [])
                
                kept_html = "".join([f"<span style='background: rgba(16, 185, 129, 0.2); color: #6EE7B7; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 700; margin: 0 6px 8px 0; display: inline-block; border: 1px solid #10B981; box-shadow: 0 1px 2px rgba(0,0,0,0.1);'>{w}</span>" for w in kept])
                dropped_html = "".join([f"<span style='background: rgba(239, 68, 68, 0.2); color: #FCA5A5; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 700; margin: 0 6px 8px 0; display: inline-block; border: 1px solid #EF4444; text-decoration: line-through; opacity: 0.85;'>{w}</span>" for w in dropped])
                
                display_kept = kept_html if kept_html else "<span style='color: #94A3B8; font-style: italic;'>None</span>"
                st.markdown(f"<div style='margin-bottom: 15px;'><strong style='color: #F8FAFC; font-size: 1.05rem;'>✅ Successfully Integrated ({len(kept)})</strong><div style='margin-top: 10px;'>{display_kept}</div></div>", unsafe_allow_html=True)
                
                if dropped:
                    st.markdown(f"<div><strong style='color: #F8FAFC; font-size: 1.05rem;'>❌ Dropped by Critic ({len(dropped)})</strong><div style='margin-top: 10px;'>{dropped_html}</div></div>", unsafe_allow_html=True)

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
                    
                    log_html += f"""<div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 3px solid {border_color}; border-radius: 6px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; gap: 10px;">
    <div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="background: rgba(255,255,255,0.08); color: #F8FAFC; padding: 2px 7px; border-radius: 4px; font-size: 0.75rem; font-weight: 700;">Req #{r_num}</span>
            <span style="color: #94A3B8; font-size: 0.8rem;">Loop {r_loop}</span>
            <strong style="color: #F8FAFC; font-size: 0.9rem;">{r_agent}</strong>
        </div>
        <div style="color: #CBD5E1; font-size: 0.85rem; margin-top: 4px;">{r_action}</div>
    </div>
    <div style="flex-shrink: 0;">
        <span style="background: rgba(59, 130, 246, 0.15); color: #93C5FD; padding: 3px 8px; border-radius: 12px; font-size: 0.75rem; font-family: monospace; border: 1px solid rgba(59, 130, 246, 0.3);">{r_model}</span>
    </div>
</div>"""
                log_html += "</div>"
                st.markdown(log_html, unsafe_allow_html=True)
        else:
            st.info("👈 Enter your draft lyrics and click **Start Refinement Pipeline** to run the multi-agent critique and optimization.")

    # Full-width Line-by-Line Breakdown across both sides (spans full page width in 2-column grid)
    if current_report:
        lines = current_report.get("line_breakdown", [])
        if lines:
            st.divider()
            
            # Quick summary metrics for the breakdown
            total_lines = len(lines)
            passed_lines = sum(1 for l in lines if l.get("status") == "✅")
            warn_lines = sum(1 for l in lines if l.get("status") not in ["✅", "❌", "🗑️"])
            flagged_lines = sum(1 for l in lines if l.get("status") in ["❌", "🗑️"])
            
            # Prepare full copyable breakdown text for external AI
            theme_val = st.session_state.get("selected_domain", "Street & Daily Life")
            genre_val = st.session_state.get("selected_genre", "Cinematic / Ballad")
            concept_val = st.session_state.get("refine_concept") or st.session_state.get("custom_concept", "")
            concept_val = re.sub(r"\bmates\b", "friends", concept_val, flags=re.I)
            concept_val = re.sub(r"\bmate\b", "friend", concept_val, flags=re.I)
            
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
                flagged_badge = f'<span style="background: rgba(239, 68, 68, 0.15); color: #FCA5A5; padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; border: 1px solid rgba(239, 68, 68, 0.3);">❌ {flagged_lines} Flagged</span>'
            else:
                flagged_badge = '<span style="background: rgba(16, 185, 129, 0.12); color: #6EE7B7; padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; border: 1px solid rgba(16, 185, 129, 0.25);">✨ 0 Flagged (Clean!)</span>'

            warn_badge = f'<span style="background: rgba(245, 158, 11, 0.15); color: #FDE68A; padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; border: 1px solid rgba(245, 158, 11, 0.3);">⚠️ {warn_lines} Polished</span>' if warn_lines else ''

            col_title, col_copy = st.columns([3.2, 1.3])
            with col_title:
                header_html = f"""<div style="margin-top: 10px; margin-bottom: 8px;">
<h3 style="margin: 0; color: #F8FAFC; font-size: 1.35rem; font-weight: 700; letter-spacing: -0.02em;">
🔍 Critic's Line-by-Line Breakdown
</h3>
<p style="margin: 4px 0 10px 0; color: #94A3B8; font-size: 0.92rem;">
Full evaluation of every lyric line scored for authenticity, natural delivery, and story coherence.
</p>
<div style="display: flex; gap: 8px; flex-wrap: wrap;">
<span style="background: rgba(255,255,255,0.06); color: #CBD5E1; padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; border: 1px solid rgba(255,255,255,0.1);">
Total: {total_lines} Lines
</span>
<span style="background: rgba(16, 185, 129, 0.15); color: #6EE7B7; padding: 4px 12px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; border: 1px solid rgba(16, 185, 129, 0.3);">
✅ {passed_lines} Passed
</span>
{warn_badge}
{flagged_badge}
</div>
</div>"""
                st.markdown(header_html, unsafe_allow_html=True)
            with col_copy:
                st.write("")
                with st.popover("📋 نسخ التقرير بالتفاصيل", use_container_width=True):
                    st.markdown("**تقرير التقييم الشامل (السطور + السكور + التعليقات):**")
                    st.caption("اضغط أيقونة النسخ في الركن الأيمن لنسخ التقرير بالكامل وإرساله للذكاء الاصطناعي الخارجي:")
                    st.code(full_breakdown_text, language="markdown")
            
            grid_html = "<div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(440px, 1fr)); gap: 14px; width: 100%; margin-bottom: 30px;'>"
            for line_data in lines:
                status = line_data.get("status", "❓")
                text = line_data.get("line", "")
                l_score = line_data.get("score", 0)
                comment = line_data.get("comment", "")
                
                if status == "✅":
                    card_bg = "linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(15, 23, 42, 0.85) 100%)"
                    border_color = "#10B981"
                    badge_bg = "#FFFFFF"
                    badge_text_color = "#047857"
                    badge_border = "#34D399"
                    feedback_color = "#A7F3D0"
                    icon = "✅"
                elif status in ["❌", "🗑️"]:
                    card_bg = "linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(15, 23, 42, 0.85) 100%)"
                    border_color = "#EF4444"
                    badge_bg = "#FFFFFF"
                    badge_text_color = "#B91C1C"
                    badge_border = "#F87171"
                    feedback_color = "#FCA5A5"
                    icon = "❌"
                else:
                    card_bg = "linear-gradient(135deg, rgba(245, 158, 11, 0.12) 0%, rgba(15, 23, 42, 0.85) 100%)"
                    border_color = "#F59E0B"
                    badge_bg = "#FFFFFF"
                    badge_text_color = "#B45309"
                    badge_border = "#FBBF24"
                    feedback_color = "#FDE68A"
                    icon = "⚠️"

                card_html = f"""<div style="background: {card_bg}; border-left: 4px solid {border_color}; border-top: 1px solid rgba(255, 255, 255, 0.08); border-right: 1px solid rgba(255, 255, 255, 0.08); border-bottom: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 14px 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.25); display: flex; flex-direction: column; justify-content: space-between; gap: 8px;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 14px;">
        <span style="font-size: 1.05rem; font-weight: 600; color: #FFFFFF; line-height: 1.45; word-break: break-word;">{text}</span>
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

