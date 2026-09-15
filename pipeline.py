"""
pipeline.py — Song text processing and vocabulary classification pipeline.
Re-exported from domain.services.lyrics_service for backwards compatibility.
"""

from domain.services.lyrics_service import (
    clean_lyrics_text,
    process_song_text,
)

__all__ = [
    "clean_lyrics_text",
    "process_song_text",
]
