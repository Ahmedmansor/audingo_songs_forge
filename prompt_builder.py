"""
prompt_builder.py — Master Prompt and Suno Style Prompt Generator.
Re-exported from domain.services.prompt_service for backwards compatibility.
"""

from domain.services.prompt_service import (
    SUNO_GENRE_PRESETS,
    build_suno_style_prompt,
    generate_master_prompt,
)

__all__ = [
    "SUNO_GENRE_PRESETS",
    "build_suno_style_prompt",
    "generate_master_prompt",
]
