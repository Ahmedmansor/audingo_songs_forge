import streamlit as st
import time
from scripts.lyrics_graph import run_refinement_graph

def render_tab_refinement():
    st.subheader("✨ Step 4: AI Lyrics Refinement Graph (Pro Max)")
    st.markdown("<p class='sub-text'>Refine, validate, and perfect the drafted lyrics using a multi-agent AI pipeline.</p>", unsafe_allow_html=True)
    
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
        
        master_prompt_val = st.session_state.get("master_prompt", "")
        
        target_words_list = []
        if st.session_state.get("target_batch"):
            target_words_list = [w["word"] for w in st.session_state.target_batch]
        words_str = ", ".join(target_words_list) if target_words_list else ""
            
        if words_str:
            st.success(f"**Target Words ({len(target_words_list)}):** {words_str}")
        else:
            st.warning("⚠️ No target words active. Please select them in the Studio tab first.")
            
        draft = st.text_area("Paste Initial Draft Lyrics Here", height=300, placeholder="[Verse 1]\nSitting in this diner...", key="refine_draft")
        
        if st.button("Start Refinement Pipeline", type="primary", use_container_width=True):
            if draft.strip() and target_words_list:
                
                with st.spinner("Initializing Multi-Agent Graph..."):
                    progress_container = st.empty()
                    
                    def ui_callback(msg):
                        progress_container.info(msg)
                        
                    start_time = time.time()
                    final_state = run_refinement_graph(
                        draft, 
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
                    st.rerun()
            else:
                st.error("Please provide a draft and ensure target words are selected in the Studio.")
                
    with col2:
        st.markdown("##### 📊 Final Report")
        if "graph_report" in st.session_state and st.session_state.graph_report is not None:
            report = st.session_state["graph_report"]
            score = report.get("overall_score", 0)
            
            # Modern metric cards using Streamlit native columns
            m1, m2, m3 = st.columns(3)
            m1.metric("Authenticity Score", f"{score}%")
            m2.metric("Iterations", f"{report.get('iterations_used', 0)}/5")
            m3.metric("Time Taken", f"{st.session_state.get('graph_time', 0)}s")
            
            st.info(f"**Final Model Active:** `{report.get('final_model_used', 'Unknown')}`")
            
            with st.expander("📝 Final Polished Lyrics", expanded=True):
                st.text(report.get("final_lyrics", ""))
                
            with st.expander("📊 Word Integration Report"):
                kept = report.get("words_kept", [])
                dropped = report.get("words_dropped", [])
                st.success(f"**Successfully Integrated ({len(kept)}):** {', '.join(kept)}")
                if dropped:
                    st.error(f"**Dropped by Critic ({len(dropped)}):** {', '.join(dropped)}")
                    
            st.markdown("### 🔍 Critic's Line-by-Line Breakdown")
            lines = report.get("line_breakdown", [])
            if lines:
                for line_data in lines:
                    status = line_data.get("status", "❓")
                    text = line_data.get("line", "")
                    l_score = line_data.get("score", 0)
                    comment = line_data.get("comment", "")
                    
                    if status == "✅":
                        st.success(f"{status} **[{l_score}%]** {text} \n\n*{comment}*")
                    elif status == "⚠️":
                        st.warning(f"{status} **[{l_score}%]** {text} \n\n*{comment}*")
                    else:
                        st.error(f"{status} **[{l_score}%]** {text} \n\n*{comment}*")
            else:
                st.write("No line breakdown available.")
