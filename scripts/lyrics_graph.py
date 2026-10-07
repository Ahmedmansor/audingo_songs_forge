"""
lyrics_graph.py — Graph Engine for Song Lyrics Refinement and Validation
"""

import json
import logging
import re
from typing import Dict, Any, List, TypedDict, Optional
from google.genai import types
from data.services.gemini_service import get_gemini_client
from data.services.fallback_engine import generate_with_fallback, MASTER_FALLBACK_CHAIN

logger = logging.getLogger(__name__)

class LineReport(TypedDict):
    line: str
    status: str # "✅", "⚠️", "❌", "🗑️"
    score: int
    comment: str

class GraphState(TypedDict):
    draft_lyrics: str
    target_words: List[str]
    theme_category: str
    genre: str
    core_concept: str
    master_prompt: str
    validation_errors: List[str]
    iterations: int
    is_completed: bool
    final_report: Optional[Dict[str, Any]]
    active_model_index: int


def python_inspector_node(state: GraphState) -> GraphState:
    """Agent 1: Python Inspector (Counts words and line lengths)."""
    draft = state["draft_lyrics"]
    target_words = state["target_words"]
    
    # Simple lemmatization check using regex boundaries. 
    # For a real project, we'd use spaCy or NLTK. Here we do a smart regex.
    draft_lower = draft.lower()
    missing_words = []
    for word in target_words:
        # Check base word + common suffixes like s, es, ed, ing
        pattern = r'\b' + re.escape(word.lower()) + r'(s|es|ed|ing|d|er)?\b'
        if not re.search(pattern, draft_lower):
            missing_words.append(word)
            
    validation_errors = []
    if missing_words:
        validation_errors.append(f"Missing target words: {', '.join(missing_words)}")
        
    lines = [line.strip() for line in draft.split('\n') if line.strip() and not line.startswith('[')]
    for i, line in enumerate(lines):
        word_count = len(line.split())
        if word_count > 10: # Assuming 10 is the max safe length
            validation_errors.append(f"Line too long ({word_count} words): '{line}'")
            
    state["validation_errors"] = validation_errors
    return state


def authenticity_critic_node(state: GraphState) -> tuple[GraphState, Dict[str, Any]]:
    """Agent 2: The Critic (Evaluates authenticity and line scores)."""
    theme = state["theme_category"]
    genre = state["genre"]
    concept = state["core_concept"]
    master_prompt = state["master_prompt"]
    draft = state["draft_lyrics"]
    errors = state.get("validation_errors", [])
    
    prompt = f"""You are an elite linguistic critic and quality assurance agent.
    Review the following song lyrics line by line. 
    
    CONTEXTUAL ANCHORS:
    - Broad Theme: "{theme}"
    - Musical Genre: "{genre}"
    - Core Story/Concept: "{concept}"
    
    TASK:
    Evaluate if each line is an authentic, natural sentence that perfectly fits the 'Core Story/Concept' and 'Theme'.
    If a line feels robotic, forced, or awkward just to rhyme or fit a target word, mark it as rejected.
    If a target word completely destroys the realism of the scene (e.g. a political word in a romantic story), you MUST recommend dropping that word entirely.
    Additionally, review the SYSTEM PRE-ANALYSIS REPORT below. If the Python inspector flagged a line as 'too long', you must mark that line as ❌ and instruct the Editor to shorten it to 5-8 words.

    SYSTEM PRE-ANALYSIS REPORT (Python word-count & missing words):
    {json.dumps(errors, indent=2)}
    
    SONG LYRICS:
    {draft}
    
    OUTPUT JSON SCHEMA:
    {{
        "overall_score": 0-100,
        "dropped_words": ["word1", "word2"], 
        "dropped_reasons": {{"word1": "reason"}},
        "lines_review": [
            {{
                "line": "the exact line text",
                "status": "✅" (Perfect), "⚠️" (Acceptable but could be better), "❌" (Rejected/Awkward), "🗑️" (Drop the target word here),
                "score": 0-100,
                "comment": "Brief reason"
            }}
        ]
    }}
    """
    
    try:
        raw_response, new_model_idx = generate_with_fallback(
            prompt, 
            start_index=state["active_model_index"], 
            require_json=True
        )
        state["active_model_index"] = new_model_idx
        critic_report = json.loads(raw_response)
        return state, critic_report
    except Exception as e:
        logger.error(f"Critic node failed: {e}")
        # Fallback empty report
        return state, {"overall_score": 0, "dropped_words": [], "lines_review": []}


def editor_refiner_node(state: GraphState, critic_report: Dict[str, Any]) -> GraphState:
    """Agent 3: The Editor (Fixes the draft)."""
    theme = state["theme_category"]
    genre = state["genre"]
    concept = state["core_concept"]
    master_prompt = state["master_prompt"]
    draft = state["draft_lyrics"]
    errors = state["validation_errors"]
    
    rejected_lines = [r for r in critic_report.get("lines_review", []) if r.get("status") in ["❌", "🗑️"]]
    dropped_words = critic_report.get("dropped_words", [])
    
    prompt = f"""You are a master songwriter fixing a flawed draft.
    Theme: {theme}
    Genre: {genre}
    Core Story: {concept}
    
    Current Draft:
    {draft}
    
    Python Inspector Errors:
    {json.dumps(errors)}
    
    Critic Rejected Lines to Fix:
    {json.dumps(rejected_lines)}
    
    Words to permanently drop (do not try to include these):
    {json.dumps(dropped_words)}
    
    TASK: Rewrite ONLY the flawed parts to fix the inspector errors and the critic's rejections. 
    Ensure perfect natural phrasing and preserve the rhyme scheme.
    Return ONLY the complete updated song lyrics text (no markdown, no extra chat).
    """
    
    try:
        raw_response, new_model_idx = generate_with_fallback(
            prompt, 
            start_index=state["active_model_index"]
        )
        state["active_model_index"] = new_model_idx
        state["draft_lyrics"] = raw_response
    except Exception as e:
        logger.error(f"Editor node failed: {e}")
        
    return state


def run_refinement_graph(draft: str, target_words: List[str], theme: str, genre: str, concept: str, master_prompt: str, progress_callback=None) -> GraphState:
    """Main Graph Execution Loop"""
    state: GraphState = {
        "draft_lyrics": draft,
        "target_words": target_words,
        "theme_category": theme,
        "genre": genre,
        "core_concept": concept,
        "master_prompt": master_prompt,
        "validation_errors": [],
        "iterations": 0,
        "is_completed": False,
        "final_report": None,
        "active_model_index": 0
    }
    
    max_iterations = 5
    last_critic_report = None
    
    for i in range(max_iterations):
        state["iterations"] = i + 1
        
        if progress_callback:
            progress_callback(f"Running iteration {i+1}... (Model: {MASTER_FALLBACK_CHAIN[state['active_model_index']]})")
            
        # 1. Inspector
        state = python_inspector_node(state)
        
        # 2. Critic
        state, critic_report = authenticity_critic_node(state)
        last_critic_report = critic_report
        
        score = critic_report.get("overall_score", 0)
        has_rejected = any(r.get("status") in ["❌", "🗑️"] for r in critic_report.get("lines_review", []))
        
        if not state["validation_errors"] and not has_rejected and score >= 90:
            state["is_completed"] = True
            break
            
        # 3. Editor
        if i < max_iterations - 1:
            state = editor_refiner_node(state, critic_report)
            
    # Final Report Generation
    state["is_completed"] = True
    
    final_words_found = [w for w in target_words if w not in (last_critic_report.get("dropped_words", []) if last_critic_report else [])]
    
    state["final_report"] = {
        "final_lyrics": state["draft_lyrics"],
        "overall_score": last_critic_report.get("overall_score", 0) if last_critic_report else 0,
        "words_kept": final_words_found,
        "words_dropped": last_critic_report.get("dropped_words", []) if last_critic_report else [],
        "line_breakdown": last_critic_report.get("lines_review", []) if last_critic_report else [],
        "iterations_used": state["iterations"],
        "final_model_used": MASTER_FALLBACK_CHAIN[state["active_model_index"]]
    }
    
    return state
