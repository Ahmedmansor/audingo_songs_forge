import sys
import os

sys.path.insert(0, os.path.abspath("."))
from constants import SONG_STRUCTURES
from domain.services.prompt_service import parse_song_structure

with open("test_output.txt", "w", encoding="utf-8") as f:
    for s in SONG_STRUCTURES:
        f.write(f"\n--- {s} ---\n")
        f.write(parse_song_structure(s) + "\n")
