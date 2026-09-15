"""
gemini_client.py — Gemini API client.
Re-exported from data.services.gemini_service for backwards compatibility.
"""

from data.services.gemini_service import (
    PREFERRED_MODELS,
    get_gemini_client,
    build_analysis_prompt,
    analyze_vocabulary_mood,
    build_poster_prompt_instruction,
    generate_poster_prompt,
    generate_studio_poster_prompt,
    build_variant_instruction,
    generate_track_variant,
    curate_thematic_vocabulary_batch,
)

__all__ = [
    "PREFERRED_MODELS",
    "get_gemini_client",
    "build_analysis_prompt",
    "analyze_vocabulary_mood",
    "build_poster_prompt_instruction",
    "generate_poster_prompt",
    "generate_studio_poster_prompt",
    "build_variant_instruction",
    "generate_track_variant",
    "curate_thematic_vocabulary_batch",
]
