"""
fallback_engine.py — Centralized API Fallback Router for the entire project.
"""

import json
import logging
import time
from typing import Optional, Dict, Any, Tuple, List
from google.genai import types
from data.services.gemini_service import get_gemini_client, get_gemini_api_keys

logger = logging.getLogger(__name__)

# User-selected quality priority for criticism and thematic vocabulary selection.
# Exhaust all configured keys on each model before moving to the next model.
# Never fall through to a generic alias, 3.5 or Lite on this route.
CRITIC_FALLBACK_CHAIN = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
]

# Dedicated Routine Studio Chain: Used for auxiliary utilities (like poster prompts and style tags).
# Core curation (Smart Thematic Pull), Mood Analysis, Word-Fit Audit, and Lyrics Critic all use CRITIC_FALLBACK_CHAIN.
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
    Quality requests always start at 3.8/key 1, then try remaining keys before 3.7/3.6.
    Routine requests retain round-robin key rotation and their separate model chain.
    For each model, attempts across all available keys before falling back to the next model.
    When a specific model_chain is provided (e.g. CRITIC_FALLBACK_CHAIN), it starts from index 0 by default.
    Returns a tuple of (response_text, successful_model_index).
    """
    global _LAST_WORKING_INDEX, _KEY_ROTATION_COUNTER
    
    keys = get_gemini_api_keys()
    if not keys:
        raise ValueError("No Gemini API keys found in environment or .env file.")
        
    chain_to_use = model_chain if model_chain is not None else MASTER_FALLBACK_CHAIN
    quality_request = model_chain is not None and model_chain == CRITIC_FALLBACK_CHAIN
    effective_start = start_index if start_index is not None else (_LAST_WORKING_INDEX if model_chain is None else 0)
    if quality_request or effective_start >= len(chain_to_use):
        effective_start = 0

    # Build model attempt chain: try from effective_start to end, then wrap to beginning
    indices_to_try = list(range(effective_start, len(chain_to_use))) + list(range(0, effective_start))
    seen = set()
    model_indices = [i for i in indices_to_try if not (i in seen or seen.add(i))]

    # Determine key rotation order for this call (round-robin across requests)
    num_keys = len(keys)
    start_k = 0 if quality_request else _KEY_ROTATION_COUNTER % num_keys
    if not quality_request:
        _KEY_ROTATION_COUNTER += 1
    key_indices = [(start_k + i) % num_keys for i in range(num_keys)]

    for m_idx in model_indices:
        model_name = chain_to_use[m_idx]
        
        # Try all available keys on this model before falling back to a lower model
        for k_idx in key_indices:
            api_key = keys[k_idx]
            key_tag = f"Key #{k_idx + 1}"
            attempt_start = time.perf_counter()
            try:
                logger.info(f"[FallbackEngine] Attempting model {model_name} with {key_tag}")
                client = get_gemini_client(api_key=api_key)
                config = types.GenerateContentConfig(temperature=temperature)
                if quality_request:
                    # The outer router owns retries. Avoid five hidden SDK attempts
                    # on an exhausted key before trying the next configured key.
                    config.http_options = types.HttpOptions(
                        retry_options=types.HttpRetryOptions(attempts=1)
                    )
                if require_json:
                    config.response_mime_type = "application/json"
                    
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                raw = (response.text or "").strip()
                if not raw:
                    raise ValueError("The model returned no usable text.")
                
                # Clean markdown code blocks if returning JSON
                if require_json and raw.startswith("```"):
                    lines = raw.splitlines()
                    raw = "\n".join(line for line in lines if not line.strip().startswith("```")).strip()
                    
                if model_chain is None:
                    _LAST_WORKING_INDEX = m_idx
                logger.info(
                    "[FallbackEngine] Model %s succeeded with %s in %.1fs",
                    model_name, key_tag, time.perf_counter() - attempt_start,
                )
                return raw, m_idx
                
            except Exception as e:
                error_message = str(e)
                for secret in keys:
                    error_message = error_message.replace(secret, "[REDACTED]")
                logger.warning(
                    "[FallbackEngine] Model %s failed with %s after %.1fs (code=%s): %s. "
                    "Trying next available key or fallback model...",
                    model_name, key_tag, time.perf_counter() - attempt_start,
                    getattr(e, "code", None), error_message,
                )
                continue
                
    if quality_request:
        raise RuntimeError(
            "Critical models failed across all configured keys (3.8 Flash -> 3.7 Flash -> 3.6 Flash). "
            "No lower model was used. See attempt logs for error codes and elapsed times."
        )
    raise RuntimeError("All models and API keys in the fallback chain have failed. See attempt logs for details.")

