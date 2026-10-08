import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, TypedDict, Optional
from google.genai import types
from data.services.gemini_service import get_gemini_client
from data.services.fallback_engine import generate_with_fallback, MASTER_FALLBACK_CHAIN
from domain.services.prompt_service import ESL_GOAL_BLOCK
from constants import get_category_profile

logger = logging.getLogger(__name__)

def compute_line_status(score: int) -> tuple[str, str]:
    """
    Strict code-based thresholding:
    🟢 >= 90 (✅)
    🟡 75-89 (⚠️)
    🔴 < 75 (❌)
    """
    try:
        val = int(round(score))
    except Exception:
        val = 0
    if val >= 90:
        return "✅", "🟢"
    elif val >= 75:
        return "⚠️", "🟡"
    else:
        return "❌", "🔴"

def critic_calibration(profile: Dict[str, Any]) -> str:
    """Shared rubric for critic-only and refinement-loop evaluations."""
    return """REGISTER AND FAIR SCORING:
- Natural English includes educated and moderately formal speech when appropriate to the speaker and situation. Everyday meaning does not mean street slang.
- Basic / Neutral vocabulary is valid in every category. Judge actual meaning and context, not category labels.
- Ordinary pronouns and references are valid when clear in a real situation; the standalone test does not require every line to retell the story.
- Normal chorus repetition is not an authenticity flaw. Flag repetition only if it creates a specific meaning or continuity problem.
- Support every deduction with a concrete defect.
- Do not give 90+ to a line you cannot defend. A real song rarely has every line above 90. If almost all your scores are 90+, re-check yourself.
- Do not apply multiple deductions for the same underlying defect.
- Score every sung lyric line, including repeated occurrences; omit section tags and blank lines.
- Authenticity measures only the quality of the lyric lines. Missing, unused, or dropped target words and coverage percentages must NEVER lower line scores or overall_score.
- overall_score is the rounded arithmetic mean of the line scores, with equal weight per lyric line. Coverage and dropped_words are separate information, never a penalty or bonus.
- Recommend dropping a target only for an actual contextual or usage problem, never merely for its register.
""" + profile.get("critic_guidance", "")


def average_line_score(lines: List[Dict[str, Any]]) -> int:
    """Authenticity is solely the mean of supplied numeric line scores."""
    scores = [item.get("score") for item in lines
              if isinstance(item.get("score"), (int, float))]
    return round(sum(scores) / len(scores)) if scores else 0


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
    """Agent 2: The Strict Critic (Evaluates authenticity and line scores starting at 100 with deductions)."""
    theme = state["theme_category"]
    genre = state["genre"]
    concept = state["core_concept"]
    dialect = state.get("dialect", "American English")
    draft = state["draft_lyrics"]
    errors = state.get("validation_errors", [])
    target_words = state.get("target_words", [])
    words_str = ", ".join(target_words) if target_words else "None specified"
    p = get_category_profile(theme)
    
    prompt = f"""You are a strict ESL lyric critic. You do NOT rewrite anything. Score each line from 0 to 100 against THE GOAL below.
Judge each line in the context of the whole song (so you can catch contradictions), but score only that line.

{ESL_GOAL_BLOCK}

CONTEXTUAL ANCHORS:
- Theme: "{theme}"
- Category guidance: Setting: {p['setting']}. Register: {p['register']}.
- Musical Genre: "{genre}"
- Core Story / Setting: "{concept}"
- Dialect: {dialect}
- Target words (the only words that count as target words): {words_str}

{critic_calibration(p)}

Start every line at 100 and subtract:
- Not something a native speaker would say in this setting (poetic, literary, inverted word order): -25
- Filler added for rhyme or rhythm, or vague when read alone ("I hope that you can see"): -20
- Fails the standalone test (not useful or not understandable on its own): -20
- Target word used in a forced, odd or non-everyday way (apply only to the target words above): -25
- Contradicts the story or the narrator's stance, or jumps outside the story/setting: -25
- Stiff form where a contraction is natural in this setting ("I am sorry", "do not"): -10
- Mixes dialects in the line, or uses forms outside {dialect}: -15
- Longer than 9 syllables or hard to sing/memorize: -10
- Crude language beyond ordinary expressions: -20

Rules:
- If any deduction applies, the score cannot exceed 89. A line with no deductions scores 90-100.
- Apply the target-word deduction only to the official target words listed above.
- For each line return: number, the line, score, and a short issue (or "none").
- If a target word completely destroys the realism of the scene or sounds forced, list it in dropped_words.

SYSTEM INSPECTOR FLAGS (Reference only):
{json.dumps(errors, indent=2)}

SONG LYRICS TO EVALUATE:
{draft}

OUTPUT JSON SCHEMA:
{{
    "overall_score": 0-100,
    "dropped_words": ["word1"],
    "dropped_reasons": {{"word1": "reason"}},
    "lines_review": [
        {{
            "number": 1,
            "line": "exact line text",
            "score": 0-100,
            "issue": "short reason or 'none'"
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
        
        # Enforce code-based thresholding and status calculation
        lines_review = critic_report.get("lines_review", [])
        if lines_review:
            for idx, item in enumerate(lines_review, 1):
                raw_score = item.get("score", 70)
                status_icon, color_circle = compute_line_status(raw_score)
                item["status"] = status_icon
                item["color"] = color_circle
                issue_val = item.get("issue") or item.get("comment") or "none"
                item["comment"] = issue_val
                item["issue"] = issue_val
                if "number" not in item:
                    item["number"] = idx
            
        critic_report["overall_score"] = average_line_score(lines_review)
        
        # Log this request
        if "execution_log" not in state:
            state["execution_log"] = []
        state["execution_log"].append({
            "request_num": state["total_requests"],
            "loop": state.get("iterations", 1),
            "agent": "Critic Agent (الناقد الصارم)",
            "model": MASTER_FALLBACK_CHAIN[new_model_idx],
            "action": f"Scored lyrics: {critic_report.get('overall_score', 0)}% ({len(critic_report.get('lines_review', []))} lines evaluated)"
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
        return state, {"overall_score": 0, "dropped_words": [], "lines_review": []}


def editor_refiner_node(state: GraphState, critic_report: Dict[str, Any]) -> GraphState:
    """Agent 3: The Editor (Fixes the draft based on strict critique)."""
    theme = state["theme_category"]
    genre = state["genre"]
    concept = state["core_concept"]
    draft = state["draft_lyrics"]
    errors = state["validation_errors"]
    
    critical_rejections = [r for r in critic_report.get("lines_review", []) if r.get("score", 0) < 75 or r.get("status") in ["❌", "🗑️"]]
    minor_warnings = [r for r in critic_report.get("lines_review", []) if 75 <= r.get("score", 0) < 90 or r.get("status") == "⚠️"]
    dropped_words = state.get("permanently_dropped_words", [])
    
    prompt = f"""You are an expert English linguist and a professional ESL teacher who edits song lyrics for learners.
Your mission is to perform SURGICAL REPAIRS on the song lyrics below.

{ESL_GOAL_BLOCK}

Theme: {theme}
Genre: {genre}
Core Story: {concept}
Dialect: American English (never mix dialects; replace British-only words like "mate" unless they are target words in locked lines)

Current Draft:
{draft}

Python Inspector Errors (Length / Missing Words):
{json.dumps(errors)}

CRITICAL FLAWED LINES (Must be rewritten - Score < 75%):
{json.dumps(critical_rejections)}

MINOR LINES (Only tweak if it can be done effortlessly - Score 75-89%):
{json.dumps(minor_warnings)}

Words to permanently drop (do not try to include these):
{json.dumps(dropped_words)}

SURGICAL REPAIR RULES:
- RULE 1 (PRESERVE VERIFIED LINES): DO NOT alter or rewrite lines that scored 90%+ (🟢 / ✅). Keep them intact!
- RULE 2 (KILL FORCED RHYMES): Lines marked ❌ (< 75%) contain awkward forced rhymes. Replace them with 100% natural, everyday spoken English.
- RULE 3 (PRACTICAL USABILITY & CONTRACTIONS): Use natural contractions (I'm, don't, can't); avoid stiff forms. Every line must pass the Standalone test.
- RULE 4 (Length & Rhythm): 6 to 9 syllables per edited line (±1).
- RULE 5 (SETTING CONTINUITY): Stay strictly inside the song's established location/time. Never introduce random disconnected places just to rhyme.
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


def run_refinement_graph(draft: str, target_words: List[str], theme: str, genre: str, concept: str, master_prompt: str, dialect: str = "American English", progress_callback=None) -> GraphState:
    """Main Graph Execution Loop"""
    state: GraphState = {
        "draft_lyrics": draft,
        "target_words": target_words,
        "theme_category": theme,
        "genre": genre,
        "core_concept": concept,
        "master_prompt": master_prompt,
        "dialect": dialect,
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
        
        # Stop early when no ❌ rejections remain, no structural/length errors exist, and score is high (>= 90%)
        if not structural_or_length_errors and not has_rejected and score >= 90:
            state["is_completed"] = True
            break
            
        # 3. Editor
        if i < max_iterations - 1:
            state = editor_refiner_node(state, critic_report)
            
    # Final Report Generation
    state["is_completed"] = True
    
    final_words_found = [w for w in target_words if w not in state.get("permanently_dropped_words", [])]
    
    state["final_report"] = {
        "input_lyrics": draft,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "context": {"concept": concept, "genre": genre, "dialect": dialect, "target_words": list(target_words), "domain": theme},
        "final_lyrics": state["draft_lyrics"],
        "overall_score": last_critic_report.get("overall_score", 0) if last_critic_report else 0,
        "critic_name": get_category_profile(theme)["critic_name"],
        "domain": theme,
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


def run_critic_only(
    draft: str,
    target_words: List[str],
    theme: str,
    genre: str,
    concept: str,
    master_prompt: str = "",
    dialect: str = "American English"
) -> Dict[str, Any]:
    """
    Mode: Critic Only (وضع الناقد فقط)
    Runs ONLY the strict critic node:
    - No inspector errors blocking or altering
    - No editor node, no loops, no automated rewriting
    - Every line scored starting from 100 with deduction rules
    - Code strictly computes color & status: 🟢 >= 90, 🟡 75-89, 🔴 < 75
    - Returns full breakdown with line, score, color, status, comment/issue, and overall score
    """
    start_time = time.time()
    words_str = ", ".join(target_words) if target_words else "None specified"
    p = get_category_profile(theme)
    
    prompt = f"""You are a strict ESL lyric critic. You do NOT rewrite anything. Score each line from 0 to 100 against THE GOAL below.
Judge each line in the context of the whole song (so you can catch contradictions), but score only that line.

{ESL_GOAL_BLOCK}

CONTEXTUAL ANCHORS:
- Theme: "{theme}"
- Category guidance: Setting: {p['setting']}. Register: {p['register']}.
- Musical Genre: "{genre}"
- Core Story / Setting: "{concept}"
- Dialect: {dialect}
- Target words (the only words that count as target words): {words_str}

{critic_calibration(p)}

Start every line at 100 and subtract:
- Not something a native speaker would say in this setting (poetic, literary, inverted word order): -25
- Filler added for rhyme or rhythm, or vague when read alone ("I hope that you can see"): -20
- Fails the standalone test (not useful or not understandable on its own): -20
- Target word used in a forced, odd or non-everyday way (apply only to the target words above): -25
- Contradicts the story or the narrator's stance, or jumps outside the story/setting: -25
- Stiff form where a contraction is natural in this setting ("I am sorry", "do not"): -10
- Mixes dialects in the line, or uses forms outside {dialect}: -15
- Longer than 9 syllables or hard to sing/memorize: -10
- Crude language beyond ordinary expressions: -20

Rules:
- If any deduction applies, the score cannot exceed 89. A line with no deductions scores 90-100.
- Apply the target-word deduction only to the official target words listed above.
- For each line return: number, the line, score, and a short issue (or "none").
- If a target word completely destroys the realism of the scene or sounds forced, list it in dropped_words.

SONG LYRICS TO EVALUATE:
{draft}

OUTPUT JSON SCHEMA:
{{
    "overall_score": 0-100,
    "dropped_words": ["word1"],
    "dropped_reasons": {{"word1": "reason"}},
    "lines_review": [
        {{
            "number": 1,
            "line": "exact line text",
            "score": 0-100,
            "issue": "short reason or 'none'"
        }}
    ]
}}
"""

    raw_response, model_idx = generate_with_fallback(prompt, require_json=True)
    end_time = time.time()
    
    critic_report = json.loads(raw_response)
    lines_review = critic_report.get("lines_review", [])
    
    # Strictly compute color and status in Python code: 🟢 >= 90, 🟡 75-89, 🔴 < 75
    parsed_lines = []
    for idx, item in enumerate(lines_review, 1):
        raw_score = item.get("score", 70)
        status_icon, color_circle = compute_line_status(raw_score)
        issue_text = item.get("issue") or item.get("comment") or "none"
        line_text = item.get("line", "")
        
        parsed_entry = {
            "number": item.get("number", idx),
            "line": line_text,
            "score": raw_score,
            "status": status_icon,
            "color": color_circle,
            "comment": issue_text,
            "issue": issue_text
        }
        parsed_lines.append(parsed_entry)
            
    overall_score = average_line_score(parsed_lines)
    passed_count = sum(1 for l in parsed_lines if l["score"] >= 90)
    warn_count = sum(1 for l in parsed_lines if 75 <= l["score"] < 90)
    flagged_count = sum(1 for l in parsed_lines if l["score"] < 75)
    
    return {
        "overall_score": overall_score,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "context": {"concept": concept, "genre": genre, "dialect": dialect, "target_words": list(target_words), "domain": theme},
        "critic_name": p["critic_name"],
        "domain": theme,
        "line_breakdown": parsed_lines,
        "passed_count": passed_count,
        "warn_count": warn_count,
        "flagged_count": flagged_count,
        "dropped_words": critic_report.get("dropped_words", []),
        "raw_lyrics": draft,
        "model_used": MASTER_FALLBACK_CHAIN[model_idx],
        "time_taken": round(end_time - start_time, 1)
    }

