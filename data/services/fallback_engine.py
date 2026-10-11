"""
fallback_engine.py — Centralized API Fallback Router for the entire project.
"""

import json
import logging
from typing import Optional, Dict, Any, Tuple, List
from google.genai import types
from data.services.gemini_service import get_gemini_client, get_gemini_api_keys

logger = logging.getLogger(__name__)

# Ordered from STRONGEST to WEAKEST
# The system will always try the strongest first. If it fails (quota/limits), 
# it gracefully degrades to the next available model.
# Dedicated Critic Fallback Chain: Prioritizes Gemini 3.8 Flash, 3.7 Flash, and 3.6 Flash for sharp, strict critique
CRITIC_FALLBACK_CHAIN = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
]

# Dedicated Routine Studio Chain: Prioritizes fast, lightweight models (3.5-flash, 3.5-flash-lite, 3.1-flash-lite)
# to conserve top model quotas/tokens and provide instant responses for Smart Thematic Pull and Mood Analysis.
# Strong models (3.6, 3.7, 3.8) are placed strictly at the end as an emergency safety net.
ROUTINE_STUDIO_CHAIN = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
]

MASTER_FALLBACK_CHAIN = ROUTINE_STUDIO_CHAIN

_LAST_WORKING_INDEX: int = 0
_KEY_ROTATION_COUNTER: int = 0


def generate_with_fallback(
    prompt: str, 
    start_index: Optional[int] = None, 
    require_json: bool = False,
    temperature: float = 0.7,
    model_chain: Optional[List[str]] = None,
) -> Tuple[str, int]:
    """
    Central API router with Multi-Key Rotation and Model Fallback.
    Rotates across all available API keys (e.g. GEMINI_API_KEY, GEMINI_API_KEY_2).
    For each model, attempts across all available keys before falling back to the next model.
    When a specific model_chain is provided (e.g. CRITIC_FALLBACK_CHAIN), it starts from index 0 by default.
    Returns a tuple of (response_text, successful_model_index).
    """
    global _LAST_WORKING_INDEX, _KEY_ROTATION_COUNTER
    
    keys = get_gemini_api_keys()
    if not keys:
        raise ValueError("No Gemini API keys found in environment or .env file.")
        
    chain_to_use = model_chain if model_chain is not None else MASTER_FALLBACK_CHAIN
    effective_start = start_index if start_index is not None else (_LAST_WORKING_INDEX if model_chain is None else 0)
    if effective_start >= len(chain_to_use):
        effective_start = 0

    # Build model attempt chain: try from effective_start to end, then wrap to beginning
    indices_to_try = list(range(effective_start, len(chain_to_use))) + list(range(0, effective_start))
    seen = set()
    model_indices = [i for i in indices_to_try if not (i in seen or seen.add(i))]

    # Determine key rotation order for this call (round-robin across requests)
    num_keys = len(keys)
    start_k = _KEY_ROTATION_COUNTER % num_keys
    _KEY_ROTATION_COUNTER += 1
    key_indices = [(start_k + i) % num_keys for i in range(num_keys)]

    for m_idx in model_indices:
        model_name = chain_to_use[m_idx]
        
        # Try all available keys on this model before falling back to a lower model
        for k_idx in key_indices:
            api_key = keys[k_idx]
            key_tag = f"Key #{k_idx + 1}"
            try:
                logger.info(f"[FallbackEngine] Attempting model {model_name} with {key_tag}")
                client = get_gemini_client(api_key=api_key)
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
                    
                if model_chain is None:
                    _LAST_WORKING_INDEX = m_idx
                return raw, m_idx
                
            except Exception as e:
                logger.warning(
                    f"[FallbackEngine] Model {model_name} failed with {key_tag}: {e}. "
                    f"Trying next available key or fallback model..."
                )
                continue
                
    raise Exception("Critical Error: All models and API keys in the fallback chain have been exhausted or failed.")

