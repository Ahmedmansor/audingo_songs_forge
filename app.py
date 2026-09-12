"""
app.py — Audingo Songs Forge Streamlit Application.
Full NGSL Vocabulary Tracking & Song Production Pipeline.
"""

import os
import streamlit as st
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables (such as GEMINI_API_KEY)
load_dotenv()

from constants import GENRES, SONG_STRUCTURES, MOOD_CATEGORIES
import db
import pipeline
import prompt_builder
import gemini_client

# Page configuration
st.set_page_config(
    page_title="Audingo Songs Forge | NGSL Studio",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for polished look
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #4F46E5, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .word-card {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        color: #0F172A !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
    }
    .word-card span, .word-card b, .word-card strong {
        color: #0F172A !important;
        font-size: 1.02rem;
    }
    .badge-noun {
        background-color: #E0E7FF !important;
        color: #1E1B4B !important;
        padding: 3px 8px !important;
        border-radius: 6px !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
    }
    .badge-verb {
        background-color: #DCFCE7 !important;
        color: #064E3B !important;
        padding: 3px 8px !important;
        border-radius: 6px !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
    }
    .badge-adj {
        background-color: #FEF3C7 !important;
        color: #78350F !important;
        padding: 3px 8px !important;
        border-radius: 6px !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
    }
    .report-card-green {
        background-color: #F0FDF4 !important;
        border: 1px solid #86EFAC !important;
        border-radius: 8px !important;
        padding: 12px !important;
        margin-bottom: 12px !important;
        color: #064E3B !important;
    }
    .report-card-green h4, .report-card-green p, .report-card-green small, .report-card-green code {
        color: #064E3B !important;
    }
    .report-card-red {
        background-color: #FEF2F2 !important;
        border: 1px solid #FCA5A5 !important;
        border-radius: 8px !important;
        padding: 12px !important;
        margin-bottom: 12px !important;
        color: #7F1D1D !important;
    }
    .report-card-red h4, .report-card-red p, .report-card-red small, .report-card-red code {
        color: #7F1D1D !important;
    }
    .report-card-blue {
        background-color: #EFF6FF !important;
        border: 1px solid #93C5FD !important;
        border-radius: 8px !important;
        padding: 12px !important;
        margin-bottom: 12px !important;
        color: #1E3A8A !important;
    }
    .report-card-blue h4, .report-card-blue p, .report-card-blue small, .report-card-blue code {
        color: #1E3A8A !important;
    }
    .report-card-yellow {
        background-color: #FEFCE8 !important;
        border: 1px solid #FDE047 !important;
        border-radius: 8px !important;
        padding: 12px !important;
        margin-bottom: 12px !important;
        color: #713F12 !important;
    }
    .report-card-yellow h4, .report-card-yellow p, .report-card-yellow small, .report-card-yellow code {
        color: #713F12 !important;
    }
</style>
""", unsafe_allow_html=True)


# Initialize SQLite DB
db.init_db()


# Cached spaCy loader
@st.cache_resource(show_spinner="Loading NLP Models...")
def load_nlp():
    import spacy
    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        from spacy.cli import download
        download("en_core_web_sm")
        return spacy.load("en_core_web_sm")


nlp = load_nlp()

# Session State Initialization
if "target_batch" not in st.session_state:
    st.session_state.target_batch = []

if "mood_analysis" not in st.session_state:
    st.session_state.mood_analysis = None

if "master_prompt" not in st.session_state:
    st.session_state.master_prompt = ""

if "selected_genre" not in st.session_state:
    st.session_state.selected_genre = GENRES[0]

if "selected_structure" not in st.session_state:
    st.session_state.selected_structure = SONG_STRUCTURES[0]

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

if "raw_lyrics_input" not in st.session_state:
    st.session_state.raw_lyrics_input = ""

if "song_title_input" not in st.session_state:
    st.session_state.song_title_input = ""


# Sidebar info
with st.sidebar:
    st.markdown("### 🎙️ Audingo Songs Forge")
    st.markdown("Automated NGSL vocabulary tracking & songwriting master prompt pipeline.")
    
    # Progress overview in sidebar
    stats = db.get_progress_stats()
    st.metric(label="Total NGSL Words", value=f"{stats['total']:,}")
    st.metric(label="Mastered / Used", value=f"{stats['used']:,}")
    st.metric(label="Unused Remaining", value=f"{stats['unused']:,}")
    st.metric(label="Extra Words Discovered", value=f"{stats['extra_count']:,}")

    api_key_set = bool(os.environ.get("GEMINI_API_KEY"))
    if api_key_set:
        st.success("🔑 Gemini API Key configured")
    else:
        st.warning("⚠️ GEMINI_API_KEY not found in .env")


# Header
st.markdown('<div class="main-header">Audingo Songs Forge</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">NGSL Vocabulary Targeting, AI Prompt Crafting, and Lyric Review Pipeline</div>', unsafe_allow_html=True)

# 3 Primary Tabs
tab1, tab2, tab3 = st.tabs([
    "📊 Dictionary & Analytics",
    "🎧 Studio (Word Selection & Prompt)",
    "🧪 Commit Lab (Review & Approval)"
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: DICTIONARY & ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("📚 Vocabulary Coverage & Dictionary Status")
    
    stats = db.get_progress_stats()
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("Total NGSL Headwords", f"{stats['total']:,}")
    with col_stat2:
        st.metric("Words Used in Songs", f"{stats['used']:,}", delta=f"{stats['percent']}%")
    with col_stat3:
        st.metric("Remaining Unused", f"{stats['unused']:,}")
    with col_stat4:
        st.metric("Extra Discovered Words", f"{stats['extra_count']:,}")

    # Progress bar
    fraction = (stats['used'] / stats['total']) if stats['total'] > 0 else 0.0
    st.progress(fraction, text=f"Coverage Progress: {stats['used']} / {stats['total']} words ({stats['percent']}%)")

    st.markdown("---")
    
    # Tables
    col_ngsl, col_extra = st.columns([1.3, 1])
    
    with col_ngsl:
        st.markdown("#### 📖 NGSL Dictionary")
        ngsl_df = db.get_all_ngsl_words()
        
        if not ngsl_df.empty:
            # Add Status column
            ngsl_df["Status"] = ngsl_df["usage_count"].apply(lambda c: "✅ Used" if c > 0 else "⏳ Unused")
            
            # Filters
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                pos_filter = st.selectbox("Filter POS", ["All", "Noun", "Verb", "Adjective", "Other"])
            with f_col2:
                status_filter = st.selectbox("Filter Status", ["All", "Used", "Unused"])
            with f_col3:
                search_word = st.text_input("Search Word", placeholder="Type word...")

            filtered_df = ngsl_df.copy()
            if pos_filter != "All":
                filtered_df = filtered_df[filtered_df["pos_type"] == pos_filter]
            if status_filter == "Used":
                filtered_df = filtered_df[filtered_df["usage_count"] > 0]
            elif status_filter == "Unused":
                filtered_df = filtered_df[filtered_df["usage_count"] == 0]
            if search_word:
                filtered_df = filtered_df[filtered_df["word"].str.contains(search_word.strip().lower(), case=False, na=False)]

            st.dataframe(
                filtered_df[["word", "pos_type", "Status", "usage_count", "lemma_family"]],
                column_config={
                    "word": "Headword",
                    "pos_type": "POS Type",
                    "Status": "Status",
                    "usage_count": "Times Used",
                    "lemma_family": "Lemma Family (Inflected Forms)"
                },
                use_container_width=True,
                height=480
            )
        else:
            st.info("Database is empty. Please run `python build_db.py` to ingest the vocabulary.")

    with col_extra:
        st.markdown("#### 🌟 Extra Words (Non-NGSL In Approved Songs)")
        extra_df = db.get_extra_words()
        if not extra_df.empty:
            st.dataframe(
                extra_df[["word", "occurrence_count", "first_seen_in_song"]],
                column_config={
                    "word": "Extra Word",
                    "occurrence_count": "Total Occurrences",
                    "first_seen_in_song": "First Seen In"
                },
                use_container_width=True,
                height=480
            )
        else:
            st.info("No extra words tracked yet. They will automatically appear when songs are approved in Commit Lab.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: STUDIO (WORD SELECTION & PROMPT GENERATION)
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("🎯 Target Word Selection & AI Prompt Generator")
    
    col_actions, col_status = st.columns([2, 1])
    with col_actions:
        b_col1, b_col2, b_col3 = st.columns([1, 1, 1.2])
        with b_col1:
            if st.button("🎲 Pull 20 Words", type="primary", use_container_width=True):
                new_batch = db.pull_20_words()
                if len(new_batch) == 20:
                    st.session_state.target_batch = new_batch
                    st.session_state.mood_analysis = None
                    st.session_state.master_prompt = ""
                    st.success("Pulled 20 unused words (10 Nouns, 6 Verbs, 4 Adjectives)!")
                    st.rerun()
                elif len(new_batch) > 0:
                    st.session_state.target_batch = new_batch
                    st.warning(f"Only {len(new_batch)} unused words available in database.")
                    st.rerun()
                else:
                    st.error("No unused words remaining in the database!")

        with b_col2:
            if st.button("🔄 Cancel & Redraw", use_container_width=True):
                new_batch = db.pull_20_words()
                st.session_state.target_batch = new_batch
                st.session_state.mood_analysis = None
                st.session_state.master_prompt = ""
                st.info("Batch redrawn.")
                st.rerun()

        with b_col3:
            if st.button("🧹 Clear Batch", use_container_width=True):
                st.session_state.target_batch = []
                st.session_state.mood_analysis = None
                st.session_state.master_prompt = ""
                st.rerun()

    # Display Active Batch
    if st.session_state.target_batch:
        current_words = [w["word"] for w in st.session_state.target_batch]
        current_ids = [w["id"] for w in st.session_state.target_batch]
        
        # Breakdown counters
        nouns_count = sum(1 for w in st.session_state.target_batch if w["pos_type"] == "Noun")
        verbs_count = sum(1 for w in st.session_state.target_batch if w["pos_type"] == "Verb")
        adjs_count = sum(1 for w in st.session_state.target_batch if w["pos_type"] == "Adjective")
        others_count = sum(1 for w in st.session_state.target_batch if w["pos_type"] not in ("Noun", "Verb", "Adjective"))

        st.caption(f"Current Batch: **{len(st.session_state.target_batch)} Words** (🔵 {nouns_count} Nouns, 🟢 {verbs_count} Verbs, 🟡 {adjs_count} Adjectives{f', ⚪ {others_count} Other' if others_count else ''})")

        # 4 columns of 5 words
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
                    # Swap button
                    if st.button(f"🔄 Swap", key=f"swap_{word_item['id']}_{idx}", help=f"Swap '{word_item['word']}' with another unused {pos}"):
                        swapped = db.swap_single_word(pos, current_ids)
                        if swapped:
                            st.session_state.target_batch[idx] = swapped
                            st.session_state.master_prompt = ""  # prompt needs regen
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
                    st.rerun()

            if st.session_state.mood_analysis:
                analysis = st.session_state.mood_analysis
                st.success(f"Analyzed using: `{analysis.get('model_used', 'Gemini')}`")
                
                if analysis.get("creative_concept"):
                    st.info(f"💡 **Concept:** {analysis['creative_concept']}")

        with col_gem2:
            if st.session_state.mood_analysis:
                analysis = st.session_state.mood_analysis
                mood_data = analysis.get("mood_breakdown", {})
                if mood_data:
                    mood_df = pd.DataFrame(list(mood_data.items()), columns=["Mood", "Percentage"])
                    mood_df = mood_df.sort_values(by="Percentage", ascending=False)
                    st.bar_chart(mood_df.set_index("Mood"), color="#4F46E5", height=220)

        # Style & Structure Selector (Initialized by Gemini, user can tweak)
        st.markdown("#### 🎛️ Tune Musical Direction")
        tune_col1, tune_col2 = st.columns(2)
        with tune_col1:
            default_genre_idx = GENRES.index(st.session_state.selected_genre) if st.session_state.selected_genre in GENRES else 0
            st.session_state.selected_genre = st.selectbox("Genre (Closed List)", GENRES, index=default_genre_idx)

        with tune_col2:
            default_struct_idx = SONG_STRUCTURES.index(st.session_state.selected_structure) if st.session_state.selected_structure in SONG_STRUCTURES else 0
            st.session_state.selected_structure = st.selectbox("Song Structure (Closed List)", SONG_STRUCTURES, index=default_struct_idx)

        # Generate Master Prompt
        st.markdown("---")
        st.subheader("📋 Step 3: Master Prompt Output")
        
        if st.button("🚀 Generate Final Prompt", type="primary", use_container_width=True):
            mood_dict = st.session_state.mood_analysis.get("mood_breakdown", {}) if st.session_state.mood_analysis else {}
            concept = st.session_state.mood_analysis.get("creative_concept", "") if st.session_state.mood_analysis else ""
            
            prompt_text = prompt_builder.generate_master_prompt(
                target_words=current_words,
                genre=st.session_state.selected_genre,
                song_structure=st.session_state.selected_structure,
                mood_analysis=mood_dict,
                creative_concept=concept
            )
            st.session_state.master_prompt = prompt_text

        if st.session_state.master_prompt:
            st.markdown("Copy the master prompt below and paste into Claude / GPT-4o to write lyrics and Suno style tags:")
            st.code(st.session_state.master_prompt, language="markdown")
    else:
        st.info("👉 Click **[Pull 20 Words]** above to select a batch of 20 unused words and begin.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: COMMIT LAB (REVIEW & APPROVAL)
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("🧪 Song Review, Text Pipeline & Word Approval")
    
    # Show active target words reminder
    if st.session_state.target_batch:
        current_target_words = [w["word"] for w in st.session_state.target_batch]
        target_display = ", ".join(f"`{w}`" for w in current_target_words)
        st.markdown(f"**Current 20 Target Words from Studio:** {target_display}")
    else:
        st.warning("⚠️ No active target batch loaded from Studio. You can still analyze a song, but target hits will be empty.")
        current_target_words = []

    st.markdown("Paste the final song lyrics generated by Suno AI / external LLM:")
    
    st.session_state.song_title_input = st.text_input(
        "Song Title",
        value=st.session_state.song_title_input,
        placeholder="e.g. Echoes of the Horizon"
    )
    
    st.session_state.raw_lyrics_input = st.text_area(
        "Song Lyrics",
        value=st.session_state.raw_lyrics_input,
        placeholder="Paste full lyrics including [Verse], [Chorus] tags here...",
        height=260
    )

    col_btn_analyze, col_btn_clear = st.columns([1.5, 3])
    with col_btn_analyze:
        if st.button("🔍 Analyze Song", type="primary", use_container_width=True):
            if not st.session_state.raw_lyrics_input.strip():
                st.error("Please paste song lyrics before analyzing.")
            else:
                with st.spinner("Executing 5-step song processing pipeline..."):
                    lemma_map = db.get_all_lemma_mappings()
                    results = pipeline.process_song_text(
                        raw_lyrics=st.session_state.raw_lyrics_input,
                        target_words=current_target_words,
                        lemma_to_headword=lemma_map,
                        nlp=nlp
                    )
                    st.session_state.analysis_results = results
                    st.rerun()

    # If results are ready, show report and approval form
    if st.session_state.analysis_results:
        res = st.session_state.analysis_results
        green_list = res.get("green", [])
        red_list = res.get("red", [])
        blue_list = res.get("blue", [])
        yellow_list = res.get("yellow", [])

        st.markdown("---")
        st.subheader("📊 Color-Coded Classification Report")
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("🟢 Target Hits", f"{len(green_list)} / {len(current_target_words)}")
        m_col2.metric("🔴 Missed Targets", f"{len(red_list)}")
        m_col3.metric("🔵 Bonus NGSL Hits", f"{len(blue_list)}")
        m_col4.metric("🟡 Extra Words", f"{len(yellow_list)}")

        st.info("Uncheck any word below if you do NOT want it counted towards the database counters.")

        # Interactive form with checkboxes
        with st.form("approval_form"):
            rep_col1, rep_col2 = st.columns(2)

            # 🟢 Green & 🔴 Red
            with rep_col1:
                # Green
                st.markdown(
                    f"""
                    <div class="report-card-green">
                        <h4>🟢 Target Hits ({len(green_list)})</h4>
                        <p><small>Target words found in song → will increment <code>usage_count</code>.</small></p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                checked_green = []
                if green_list:
                    for w in green_list:
                        if st.checkbox(f"🟢 {w}", value=True, key=f"chk_green_{w}"):
                            checked_green.append(w)
                else:
                    st.caption("No target words detected in the lyrics.")

                # Red
                st.markdown(
                    f"""
                    <div class="report-card-red">
                        <h4>🔴 Missed Targets ({len(red_list)})</h4>
                        <p><small>Target words not found in song → remains <code>usage_count = 0</code>.</small></p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if red_list:
                    st.markdown(", ".join(f"`{w}`" for w in red_list))
                else:
                    st.success("🎉 Perfect! All 20 target words were used in the song!")

            # 🔵 Blue & 🟡 Yellow
            with rep_col2:
                # Blue
                st.markdown(
                    f"""
                    <div class="report-card-blue">
                        <h4>🔵 Bonus NGSL Hits ({len(blue_list)})</h4>
                        <p><small>Incidental words from NGSL → will increment <code>usage_count</code>.</small></p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                checked_blue = []
                if blue_list:
                    for w in blue_list:
                        if st.checkbox(f"🔵 {w}", value=True, key=f"chk_blue_{w}"):
                            checked_blue.append(w)
                else:
                    st.caption("No incidental NGSL words found.")

                # Yellow
                st.markdown(
                    f"""
                    <div class="report-card-yellow">
                        <h4>🟡 Extra Words ({len(yellow_list)})</h4>
                        <p><small>Valid words not in NGSL → will be added/incremented in <code>extra_words</code>.</small></p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                checked_yellow = []
                if yellow_list:
                    for w in yellow_list:
                        if st.checkbox(f"🟡 {w}", value=True, key=f"chk_yellow_{w}"):
                            checked_yellow.append(w)
                else:
                    st.caption("No extra non-NGSL words found.")

            st.markdown("---")
            submitted = st.form_submit_button("✅ Approve & Save Song", type="primary", use_container_width=True)
            
            if submitted:
                title = st.session_state.song_title_input.strip()
                if not title:
                    title = "Untitled Song"

                all_ngsl_to_increment = checked_green + checked_blue
                
                song_id, approved_ngsl_count, approved_extra_count = db.approve_and_save_song(
                    title=title,
                    lyrics=st.session_state.raw_lyrics_input.strip(),
                    target_words=current_target_words,
                    checked_ngsl_words=all_ngsl_to_increment,
                    checked_extra_words=checked_yellow
                )

                new_stats = db.get_progress_stats()
                
                st.balloons()
                st.success(
                    f"🎉 **Song '{title}' Saved Successfully!** (Song ID #{song_id})\n\n"
                    f"- Approved **{approved_ngsl_count}** words in the main NGSL dictionary.\n"
                    f"- Approved **{approved_extra_count}** words in Extra Words.\n"
                    f"- **{new_stats['unused']:,}** words remain unused in the NGSL dictionary."
                )

                # Reset batch & form
                st.session_state.target_batch = []
                st.session_state.mood_analysis = None
                st.session_state.master_prompt = ""
                st.session_state.analysis_results = None
                st.session_state.raw_lyrics_input = ""
                st.session_state.song_title_input = ""
