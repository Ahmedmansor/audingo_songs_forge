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
    total_requests: int
    models_used_history: List[str]
    permanently_dropped_words: List[str]


def python_inspector_node(state: GraphState) -> GraphState:
    """Agent 1: Python Inspector (Counts words and line lengths)."""
    draft = state["draft_lyrics"]
    dropped = state.get("permanently_dropped_words", [])
    active_target_words = [w for w in state["target_words"] if w not in dropped]
    
    # Simple lemmatization check using regex boundaries. 
    # For a real project, we'd use spaCy or NLTK. Here we do a smart regex.
    draft_lower = draft.lower()
    missing_words = []
    for word in active_target_words:
        # Check base word + common suffixes like s, es, ed, ing
        pattern = r'\b' + re.escape(word.lower()) + r'(s|es|ed|ing|d|er)?\b'
        if not re.search(pattern, draft_lower):
            missing_words.append(word)
            
    validation_errors = []
    if missing_words:
        validation_errors.append(f"Missing target words: {', '.join(missing_words)}")
        
    tags = [line for line in draft.split('\n') if line.strip().startswith('[')]
    if not tags:
        validation_errors.append("CRITICAL ERROR: All structural tags (e.g. [Verse 1], [Chorus]) are missing! You must restore the song structure.")

    lines = [line.strip() for line in draft.split('\n') if line.strip() and not line.startswith('[')]
    for i, line in enumerate(lines):
        word_count = len(line.split())
        char_count = len(line)
        if word_count > 8: # Tightened for maximum singability
            validation_errors.append(f"Line too long ({word_count} words). Max is 8: '{line}'")
        elif char_count > 48:
            validation_errors.append(f"Line visually too long/heavy ({char_count} characters). Max is 48 chars to ensure singability: '{line}'")
            
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
    
    TASK & COHERENCE CHECK (flag as ⚠️ or ❌ if violated):
    1. THEMATIC CONSISTENCY: Every line must stay inside the song's theme ('{theme}') and central story ('{concept}'). Do not introduce topics or characters that drift away from the central conflict.
    2. SETTING CONTINUITY: Every line must stay inside the song's established location/time (e.g., a diner at 3 AM). Any sudden new location or scene (hill, beach, street, etc.) without a clear transition must be flagged as ⚠️ or ❌.
    3. PRACTICAL USABILITY: Evaluate if each line is an authentic, natural sentence that an ESL learner can actually reuse in real life. Prefer everyday spoken conversational English over poetic or literary phrasing.
    4. NO FORCED RHYME: Does the line exist only to rhyme with its pair, without adding meaning to the story? If removing it would not hurt the narrative (filler line), flag it as ⚠️ or ❌.
    5. RHYME & RHYTHM: If a line destroys the natural rhyme scheme or feels awkwardly long to sing, mark it as ⚠️ or ❌.
    6. ACTIONABLE CRITIQUE: In the 'comment', state which rule failed (e.g., 'Violates setting continuity: sudden hill reference', 'Forced rhyme filler') and suggest a fix that stays inside the song's world.
    7. TARGET WORD REALISM: If a target word completely destroys the realism of the scene (e.g. a political word in a romantic story), you MUST recommend dropping that word entirely in 'dropped_words'.
    8. LENGTH INSPECTOR: Additionally, review the SYSTEM PRE-ANALYSIS REPORT below. If the Python inspector flagged a line as 'too long', you must mark that line as ❌ and instruct the Editor to shorten it to 5-8 words.

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
        state["total_requests"] = state.get("total_requests", 0) + 1
        if "models_used" not in state: state["models_used"] = []
        state["models_used"].append(MASTER_FALLBACK_CHAIN[new_model_idx])
        
        critic_report = json.loads(raw_response)
        
        # Calculate true mathematical average from line reviews to ensure accuracy
        lines_review = critic_report.get("lines_review", [])
        if lines_review:
            valid_scores = [l.get("score") for l in lines_review if isinstance(l.get("score"), (int, float))]
            if valid_scores:
                critic_report["overall_score"] = round(sum(valid_scores) / len(valid_scores))
        
        # Log this request
        if "execution_log" not in state:
            state["execution_log"] = []
        state["execution_log"].append({
            "request_num": state["total_requests"],
            "loop": state.get("iterations", 1),
            "agent": "Critic Agent (الناقد)",
            "model": MASTER_FALLBACK_CHAIN[new_model_idx],
            "action": f"Scored lyrics: {critic_report.get('overall_score', 0)}% (Checked {len(critic_report.get('lines_review', []))} lines)"
        })
        
        new_drops = critic_report.get("dropped_words", [])
        if "permanently_dropped_words" not in state:
            state["permanently_dropped_words"] = []
        for w in new_drops:
            if w not in state["permanently_dropped_words"]:
                state["permanently_dropped_words"].append(w)
                
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
    
    critical_rejections = [r for r in critic_report.get("lines_review", []) if r.get("status") in ["❌", "🗑️"]]
    minor_warnings = [r for r in critic_report.get("lines_review", []) if r.get("status") == "⚠️"]
    dropped_words = state.get("permanently_dropped_words", [])
    
    prompt = f"""You are a master songwriter performing SURGICAL REPAIRS on song lyrics.
    Theme: {theme}
    Genre: {genre}
    Core Story: {concept}
    
    Current Draft:
    {draft}
    
    Python Inspector Errors (Length / Missing Words):
    {json.dumps(errors)}
    
    CRITICAL FLAWED LINES (Must be rewritten - Status ❌ / 🗑️):
    {json.dumps(critical_rejections)}
    
    MINOR LINES (Only tweak if it can be done effortlessly - Status ⚠️):
    {json.dumps(minor_warnings)}
    
    Words to permanently drop (do not try to include these):
    {json.dumps(dropped_words)}
    
    SURGICAL REPAIR RULES:
    - RULE 1 (PRESERVE VERIFIED LINES): DO NOT alter or rewrite lines that scored ✅. Keep them intact!
    - RULE 2 (KILL FORCED RHYMES): Lines marked ❌ contain awkward forced rhymes (e.g. 'seal our deal', 'just look how'). Replace them with 100% natural, everyday spoken English.
    - RULE 3 (NATURAL SPEECH OVER RHYME): If a rhyme feels slightly unnatural, prioritize authentic emotional conversation over forcing a rhyme.
    - RULE 4 (Rhythm): Keep lines short (5-8 words).
    - RULE 5 (SETTING CONTINUITY): Stay strictly inside the song's established location/time (e.g. diner at 3 AM). Never introduce random disconnected places (hill, beach, trees) just to rhyme.
    - RULE 6 (Structure): Maintain all structural tags like [Verse 1], [Chorus], [Bridge], [Outro].
    
    Return ONLY the complete updated song lyrics text (no markdown, no extra chat).
    """
    
    try:
        raw_response, new_model_idx = generate_with_fallback(
            prompt, 
            start_index=state["active_model_index"]
        )
        state["active_model_index"] = new_model_idx
        state["total_requests"] = state.get("total_requests", 0) + 1
        if "models_used" not in state: state["models_used"] = []
        state["models_used"].append(MASTER_FALLBACK_CHAIN[new_model_idx])
        
        state["draft_lyrics"] = raw_response
        
        # Log this request
        if "execution_log" not in state:
            state["execution_log"] = []
        state["execution_log"].append({
            "request_num": state["total_requests"],
            "loop": state.get("iterations", 1),
            "agent": "Editor Agent (المحرر)",
            "model": MASTER_FALLBACK_CHAIN[new_model_idx],
            "action": f"Rewrote flawed parts ({len(critical_rejections)} critical rejections targeted)"
        })
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
        "active_model_index": 0,
        "total_requests": 0,
        "models_used": [],
        "execution_log": [],
        "permanently_dropped_words": []
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
        
        # Structural or length errors (excluding optional missing words)
        structural_or_length_errors = [e for e in state.get("validation_errors", []) if not e.startswith("Missing target words")]
        
        # Stop early when no ❌ rejections remain, no structural/length errors exist, and score is high (>= 85%)
        if not structural_or_length_errors and not has_rejected and score >= 85:
            state["is_completed"] = True
            break
            
        # 3. Editor
        if i < max_iterations - 1:
            state = editor_refiner_node(state, critic_report)
            
    # Final Report Generation
    state["is_completed"] = True
    
    final_words_found = [w for w in target_words if w not in state.get("permanently_dropped_words", [])]
    
    state["final_report"] = {
        "final_lyrics": state["draft_lyrics"],
        "overall_score": last_critic_report.get("overall_score", 0) if last_critic_report else 0,
        "words_kept": final_words_found,
        "words_dropped": state.get("permanently_dropped_words", []),
        "line_breakdown": last_critic_report.get("lines_review", []) if last_critic_report else [],
        "iterations_used": state["iterations"],
        "final_model_used": MASTER_FALLBACK_CHAIN[state["active_model_index"]],
        "total_requests": state.get("total_requests", 0),
        "models_used": list(dict.fromkeys(state.get("models_used", []))), # deduplicate while preserving order
        "execution_log": state.get("execution_log", [])
    }
    
    return state
