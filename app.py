"""
app.py — Audingo Songs Forge Streamlit Application.
Full NGSL Vocabulary Tracking & Song Production Pipeline.
"""

import os
import json
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
    .lyrics-box {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        padding: 16px 20px !important;
        font-family: monospace !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
        white-space: pre-wrap !important;
        margin-top: 10px !important;
        margin-bottom: 12px !important;
    }
    .target-pill {
        display: inline-block !important;
        background-color: #EDE9FE !important;
        color: #4C1D95 !important;
        padding: 3px 10px !important;
        border-radius: 12px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        margin: 2px 4px !important;
    }
    .bonus-pill {
        display: inline-block !important;
        background-color: #EFF6FF !important;
        color: #1E3A8A !important;
        border: 1px solid #BFDBFE !important;
        padding: 3px 10px !important;
        border-radius: 12px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        margin: 2px 4px !important;
    }
    .extra-pill {
        display: inline-block !important;
        background-color: #FEFCE8 !important;
        color: #713F12 !important;
        border: 1px solid #FEF08A !important;
        padding: 3px 10px !important;
        border-radius: 12px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        margin: 2px 4px !important;
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

# Load active studio session state from SQLite (persists across F5 browser refreshes)
persisted_session = db.load_active_batch_state()

# Session State Initialization
if "target_batch" not in st.session_state:
    st.session_state.target_batch = persisted_session.get("target_batch", [])

if "mood_analysis" not in st.session_state:
    st.session_state.mood_analysis = persisted_session.get("mood_analysis", None)

if "master_prompt" not in st.session_state:
    st.session_state.master_prompt = persisted_session.get("master_prompt", "")

if "studio_suno_prompt" not in st.session_state:
    st.session_state.studio_suno_prompt = persisted_session.get("suno_prompt", "")

if "selected_genre" not in st.session_state:
    st.session_state.selected_genre = persisted_session.get("selected_genre", GENRES[0])

if "selected_vocalist" not in st.session_state:
    st.session_state.selected_vocalist = persisted_session.get("selected_vocalist", "Male")

if "selected_structure" not in st.session_state:
    st.session_state.selected_structure = persisted_session.get("selected_structure", SONG_STRUCTURES[0])

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

if "raw_lyrics_input" not in st.session_state:
    st.session_state.raw_lyrics_input = ""

if "song_title_input" not in st.session_state:
    st.session_state.song_title_input = ""

if "custom_concept" not in st.session_state:
    st.session_state.custom_concept = persisted_session.get("custom_concept", "")

if "commit_success_message" not in st.session_state:
    st.session_state.commit_success_message = None


def sync_active_session():
    """Sync current studio batch and musical direction to SQLite for F5 persistence."""
    if st.session_state.target_batch:
        db.save_active_batch_state(
            batch=st.session_state.target_batch,
            concept=st.session_state.get("custom_concept", ""),
            genre=st.session_state.get("selected_genre", GENRES[0]),
            song_structure=st.session_state.get("selected_structure", SONG_STRUCTURES[0]),
            mood_analysis=st.session_state.get("mood_analysis", None),
            master_prompt=st.session_state.get("master_prompt", ""),
            suno_prompt=st.session_state.get("studio_suno_prompt", ""),
            vocalist=st.session_state.get("selected_vocalist", "Male")
        )
    else:
        db.clear_active_batch_state()


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

# 4 Primary Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dictionary & Analytics",
    "🎧 Studio (Word Selection & Prompt)",
    "🧪 Commit Lab (Review & Approval)",
    "🎵 Songs Library"
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
                    st.session_state.studio_suno_prompt = ""
                    st.session_state.custom_concept = ""
                    sync_active_session()
                    st.success("Pulled 20 unused words (10 Nouns, 6 Verbs, 4 Adjectives)!")
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
            if st.button("🔄 Cancel & Redraw", use_container_width=True):
                new_batch = db.pull_20_words()
                st.session_state.target_batch = new_batch
                st.session_state.mood_analysis = None
                st.session_state.master_prompt = ""
                st.session_state.studio_suno_prompt = ""
                st.session_state.custom_concept = ""
                sync_active_session()
                st.info("Batch redrawn.")
                st.rerun()

        with b_col3:
            if st.button("🧹 Clear Batch", use_container_width=True):
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

        # Style & Structure Selector (Initialized by Gemini, user can tweak)
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

        # Generate Master Prompt & Suno Style Prompt
        st.markdown("---")
        st.subheader("📋 Step 3: Generation & Production Prompts")
        
        if st.button("🚀 Generate Final Prompt", type="primary", use_container_width=True):
            mood_dict = st.session_state.mood_analysis.get("mood_breakdown", {}) if st.session_state.mood_analysis else {}
            concept = st.session_state.custom_concept.strip() or (
                st.session_state.mood_analysis.get("creative_concept", "") if st.session_state.mood_analysis else ""
            )
            
            prompt_text = prompt_builder.generate_master_prompt(
                target_words=current_words,
                genre=st.session_state.selected_genre,
                song_structure=st.session_state.selected_structure,
                mood_analysis=mood_dict,
                creative_concept=concept
            )
            suno_text = prompt_builder.build_suno_style_prompt(
                genre=st.session_state.selected_genre,
                vocalist=st.session_state.selected_vocalist
            )
            st.session_state.master_prompt = prompt_text
            st.session_state.studio_suno_prompt = suno_text
            sync_active_session()

        if st.session_state.master_prompt:
            # ──────────────────────────────────────────────────────────
            # 1. Dedicated Suno AI Music Style Prompt Section
            # ──────────────────────────────────────────────────────────
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

            # ──────────────────────────────────────────────────────────
            # 2. Master Songwriting Prompt Section
            # ──────────────────────────────────────────────────────────
            st.markdown("#### 📝 2. Master Lyrics Prompt (Copy & Paste into Claude / GPT-4o):")
            st.caption("Full prompt containing all 20 target vocabulary words, real-world narrative concept, and strict Logic Gate:")
            st.code(st.session_state.master_prompt, language="markdown")
    else:
        st.info("👉 Click **[Pull 20 Words]** above to select a batch of 20 unused words and begin.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: COMMIT LAB (REVIEW & APPROVAL)
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("🧪 Song Review, Text Pipeline & Word Approval")
    
    # Show commit success banner if a song was just saved
    if st.session_state.get("commit_success_message"):
        msg = st.session_state.commit_success_message
        st.balloons()
        st.success(
            f"🎉 **Song '{msg['title']}' Saved Successfully!** (Song ID #{msg['song_id']})\n\n"
            f"- Approved **{msg['approved_ngsl_count']}** words in the main NGSL dictionary.\n"
            f"- Approved **{msg['approved_extra_count']}** words in Extra Words.\n"
            f"- **{msg['unused_remaining']:,}** words remain unused in the NGSL dictionary."
        )
        st.session_state.commit_success_message = None

    # Show active target words reminder
    if st.session_state.target_batch:
        current_target_words = [w["word"] for w in st.session_state.target_batch]
        target_display = ", ".join(f"`{w}`" for w in current_target_words)
        st.markdown(f"**Current 20 Target Words from Studio:** {target_display}")
    else:
        st.warning("⚠️ No active target batch loaded from Studio. If you analyze a song now, all detected NGSL words will be classified as Bonus hits (Blue), not Target hits (Green).")
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
                if not current_target_words:
                    st.caption("No target batch was active during analysis.")
                elif red_list:
                    st.markdown(", ".join(f"`{w}`" for w in red_list))
                else:
                    st.success(f"🎉 Perfect! All {len(current_target_words)} target words were used in the song!")

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
                
                # Fetch metadata to persist with song
                mood_dict = st.session_state.mood_analysis.get("mood_breakdown", {}) if st.session_state.mood_analysis else {}
                current_genre = st.session_state.selected_genre
                current_structure = st.session_state.selected_structure
                current_concept = st.session_state.custom_concept.strip() or (
                    st.session_state.mood_analysis.get("creative_concept", "") if st.session_state.mood_analysis else ""
                )

                song_id, approved_ngsl_count, approved_extra_count = db.approve_and_save_song(
                    title=title,
                    lyrics=st.session_state.raw_lyrics_input.strip(),
                    target_words=current_target_words,
                    checked_bonus_words=checked_blue,
                    checked_extra_words=checked_yellow,
                    checked_target_words=checked_green,
                    mood_breakdown=mood_dict,
                    genre=current_genre,
                    song_structure=current_structure,
                    creative_concept=current_concept
                )

                new_stats = db.get_progress_stats()

                # Reset batch & form
                st.session_state.target_batch = []
                st.session_state.mood_analysis = None
                st.session_state.master_prompt = ""
                st.session_state.custom_concept = ""
                st.session_state.analysis_results = None
                st.session_state.raw_lyrics_input = ""
                st.session_state.song_title_input = ""
                db.clear_active_batch_state()

                # Store success message and trigger instant rerun so sidebar & tabs update reactively
                st.session_state.commit_success_message = {
                    "title": title,
                    "song_id": song_id,
                    "approved_ngsl_count": approved_ngsl_count,
                    "approved_extra_count": approved_extra_count,
                    "unused_remaining": new_stats["unused"]
                }
                st.rerun()


@st.dialog("⚠️ Confirm Song Deletion")
def confirm_delete_song_dialog(song_id: int, song_title: str, row_num: int):
    """Safety confirmation modal before executing atomic delete and rollback."""
    st.markdown(f"#### 🗑️ Are you sure you want to delete Song #{row_num}?")
    st.warning(
        f"**Song Title:** {song_title}\n\n"
        f"⚠️ **Atomic Safe Rollback will occur:**\n"
        f"- Target & Bonus vocabulary will have their `usage_count` decremented (-1) in the NGSL dictionary.\n"
        f"- Non-NGSL extra words will have their occurrences decremented (-1).\n"
        f"- The song and all its recorded metadata will be permanently removed."
    )
    dlg_c1, dlg_c2 = st.columns(2)
    with dlg_c1:
        if st.button("🔥 Yes, Confirm Delete", type="primary", use_container_width=True, key=f"dlg_confirm_del_{song_id}"):
            if db.delete_song(song_id, rollback_words=True):
                st.session_state["lib_toast_msg"] = f"Song #{row_num} ('{song_title}') deleted and dictionary counters rolled back."
                st.rerun()
    with dlg_c2:
        if st.button("❌ Cancel", use_container_width=True, key=f"dlg_cancel_del_{song_id}"):
            st.rerun()


@st.dialog("⚠️ Confirm Track Variant Deletion")
def confirm_delete_variant_dialog(variant_id: int, genre: str, vocalist: str):
    """Safety confirmation modal before deleting a track variant package."""
    st.markdown("#### 🗑️ Delete Track Variant Package?")
    st.warning(
        f"Are you sure you want to delete the production package for **{genre}** ({vocalist})?\n\n"
        f"This will permanently delete both the Suno music prompt and the poster art prompt. This action cannot be undone."
    )
    dlg_c1, dlg_c2 = st.columns(2)
    with dlg_c1:
        if st.button("🔥 Yes, Delete Variant", type="primary", use_container_width=True, key=f"dlg_confirm_del_variant_{variant_id}"):
            if db.delete_track_variant(variant_id):
                st.session_state["lib_toast_msg"] = f"Track variant for '{genre}' ({vocalist}) was deleted."
                st.rerun()
    with dlg_c2:
        if st.button("❌ Cancel", use_container_width=True, key=f"dlg_cancel_del_variant_{variant_id}"):
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
        if st.button("⚡ Yes, Overwrite & Regenerate", type="primary", use_container_width=True, key=f"dlg_confirm_ovr_{song_id}_{clean_g}_{vocalist}"):
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
        if st.button("❌ Cancel", use_container_width=True, key=f"dlg_cancel_ovr_{song_id}_{clean_g}_{vocalist}"):
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: SONGS LIBRARY & ARCHIVES
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
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
        # Assign 1-based sequential row number
        songs_df = songs_df.reset_index(drop=True)
        songs_df["row_num"] = range(1, len(songs_df) + 1)

        # Metrics summary
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
                songs_df["extra_words"].str.lower().str.contains(q, na=False)
            ]

        st.caption(f"Showing **{len(filtered_df)}** of **{len(songs_df)}** saved songs:")

        for _, row in filtered_df.iterrows():
            song_id = int(row["id"])
            row_num = int(row["row_num"])
            song_title = row["title"]
            created_at = row["created_at"]
            target_words_raw = row["target_words"] or ""
            bonus_words_raw = row.get("bonus_words") or ""
            extra_words_raw = row.get("extra_words") or ""
            lyrics_text = row["lyrics"] or ""
            genre_val = row.get("genre") or ""
            structure_val = row.get("song_structure") or ""
            concept_val = row.get("creative_concept") or ""
            mood_raw = row.get("mood_breakdown") or ""

            target_list = [w.strip() for w in target_words_raw.split(",") if w.strip()]
            bonus_list = [w.strip() for w in bonus_words_raw.split(",") if w.strip()]
            extra_list = [w.strip() for w in extra_words_raw.split(",") if w.strip()]

            # Parse mood breakdown
            mood_dict = {}
            if mood_raw:
                try:
                    mood_dict = json.loads(mood_raw) if isinstance(mood_raw, str) else mood_raw
                except Exception:
                    mood_dict = {}

            with st.expander(
                f"🎵 #{row_num} — **{song_title}** ({len(target_list)} Targets • {len(bonus_list)} Bonus • {len(extra_list)} Extra) • 📅 {created_at}",
                expanded=(row_num == 1)
            ):
                # Overview columns: Vocabulary & Metrics
                info_col1, info_col2 = st.columns([3, 1])
                with info_col1:
                    # 1. Target Words
                    st.markdown(f"**🎯 Target Vocabulary ({len(target_list)}):**")
                    if target_list:
                        pills_html = " ".join(f'<span class="target-pill">{w}</span>' for w in target_list)
                        st.markdown(pills_html, unsafe_allow_html=True)
                    else:
                        st.error("⚠️ Target words are empty! Click '✏️ Edit Song Details, Words & Metadata' below to add them by hand.")

                    # 2. Bonus NGSL Hits
                    if bonus_list:
                        st.markdown(f"<div style='margin-top: 8px;'><b>🔵 Bonus NGSL Hits ({len(bonus_list)}):</b></div>", unsafe_allow_html=True)
                        bonus_html = " ".join(f'<span class="bonus-pill">{w}</span>' for w in bonus_list)
                        st.markdown(bonus_html, unsafe_allow_html=True)

                    # 3. Extra Non-NGSL Words
                    if extra_list:
                        st.markdown(f"<div style='margin-top: 8px;'><b>🟡 Extra Words ({len(extra_list)}):</b></div>", unsafe_allow_html=True)
                        extra_html = " ".join(f'<span class="extra-pill">{w}</span>' for w in extra_list)
                        st.markdown(extra_html, unsafe_allow_html=True)

                with info_col2:
                    words_in_lyrics = len(lyrics_text.split())
                    lines_in_lyrics = len([l for l in lyrics_text.splitlines() if l.strip()])
                    st.metric("Song Length", f"{words_in_lyrics} words", help=f"{lines_in_lyrics} lines")

                st.markdown("<hr style='margin: 15px 0; border-color: rgba(255,255,255,0.08);'>", unsafe_allow_html=True)

                # 💡 Story / Creative Concept
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

                # 🤖 Step 2: Gemini Flash Mood & Musical Analysis
                st.markdown("##### 🤖 Step 2: Gemini Flash Mood & Musical Analysis:")
                
                # Musical Direction cards (Genre & Structure)
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

                # Mood Profile Breakdown
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

                # Action buttons row
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

                # ──────────────────────────────────────────────────────────────
                # 💿 TRACK VARIANTS & PACKAGING (SUNO + POSTER)
                # ──────────────────────────────────────────────────────────────
                saved_variants = db.get_track_variants(song_id)
                variants_count = len(saved_variants)
                variant_expander_title = f"💿 Track Variants & Packaging ({variants_count})" if variants_count > 0 else "💿 Track Variants & Packaging"

                with st.expander(variant_expander_title, expanded=(variants_count > 0)):
                    st.markdown("##### 💿 Audio & Visual Production Package (Suno AI + Midjourney/DALL-E)")
                    st.caption(
                        "Generate unified style variations (Covers) for this song with a single click: a keyword-optimized music style prompt for Suno AI (< 120 chars, BPM, vocal clarity) paired with an aesthetic album cover prompt for Midjourney / DALL-E featuring artistic typography."
                    )

                    # Controls: Genre, Vocalist, Generate Button
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

                    # Display saved track variants
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

                            # Section 1: Suno Music Prompt
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

                            # Section 2: Poster Image Prompt
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

                            # Action buttons: Save Edits, Regenerate, Delete
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

                        e_w_col1, e_w_col2 = st.columns(2)
                        with e_w_col1:
                            new_bonuses = st.text_area(
                                "🔵 Bonus NGSL Words (comma-separated):",
                                value=bonus_words_raw,
                                placeholder="Incidental NGSL words found in song...",
                                help="Incidental words from the NGSL that appeared in the song lyrics.",
                                key=f"edit_bonuses_{song_id}"
                            )
                        with e_w_col2:
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
                                extra_words=new_extras.strip(),
                                genre=new_genre,
                                song_structure=new_structure,
                                creative_concept=new_concept.strip(),
                                sync_ngsl_usage=sync_ngsl_chk
                            )
                            st.success(f"Song #{row_num} updated successfully!")
                            st.rerun()

                    # Gemini Re-analysis helper button
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
                                        extra_words=extra_words_raw,
                                        mood_breakdown=res.get("mood_breakdown"),
                                        genre=res.get("genre", genre_val),
                                        song_structure=res.get("song_structure", structure_val),
                                        creative_concept=res.get("creative_concept", concept_val),
                                        sync_ngsl_usage=False
                                    )
                                    st.success("Gemini Mood & Story Analysis completed and saved to song!")
                                    st.rerun()
                                else:
                                    st.error(f"Gemini analysis failed: {res.get('error')}")

