"""
fallback_engine.py — Centralized API Fallback Router for the entire project.
"""

import json
import logging
from typing import Optional, Dict, Any, Tuple
from google.genai import types
from data.services.gemini_service import get_gemini_client

logger = logging.getLogger(__name__)

# Ordered from STRONGEST to WEAKEST
# The system will always try the strongest first. If it fails (quota/limits), 
# it gracefully degrades to the next available model.
MASTER_FALLBACK_CHAIN = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3-flash",
    # Real current models as ultimate safety nets
    "gemini-2.5-flash",
    "gemini-1.5-flash",
]

_LAST_WORKING_INDEX: int = 0

def generate_with_fallback(
    prompt: str, 
    start_index: Optional[int] = None, 
    require_json: bool = False,
    temperature: float = 0.7
) -> Tuple[str, int]:
    """
    Central API router. Attempts to call Gemini models sequentially starting from start_index
    or the last known working model to eliminate repeated 503 timeout delays.
    Returns a tuple of (response_text, successful_model_index).
    """
    global _LAST_WORKING_INDEX
    client = get_gemini_client()
    
    effective_start = start_index if start_index is not None else _LAST_WORKING_INDEX
    # Build attempt chain: try from effective_start to end, then wrap to beginning
    indices_to_try = list(range(effective_start, len(MASTER_FALLBACK_CHAIN))) + list(range(0, effective_start))
    seen = set()
    chain = [i for i in indices_to_try if not (i in seen or seen.add(i))]

    for idx in chain:
        model_name = MASTER_FALLBACK_CHAIN[idx]
        try:
            logger.info(f"[FallbackEngine] Attempting with model: {model_name}")
            config = types.GenerateContentConfig(temperature=temperature)
            if require_json:
                config.response_mime_type = "application/json"
                
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            raw = response.text.strip()
            
            # Clean markdown code blocks if returning JSON
            if require_json and raw.startswith("```"):
                lines = raw.splitlines()
                raw = "\n".join(line for line in lines if not line.strip().startswith("```")).strip()
                
            _LAST_WORKING_INDEX = idx
            return raw, idx
            
        except Exception as e:
            logger.warning(f"[FallbackEngine] Model {model_name} failed: {e}. Switching to next model...")
            continue
            
    raise Exception("Critical Error: All models in the fallback chain have been exhausted or failed.")

