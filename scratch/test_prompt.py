import sys, os
sys.path.insert(0, os.path.abspath("."))

from domain.services.prompt_service import generate_master_prompt

p = generate_master_prompt(
    target_words=["mom", "mistake", "mate", "listen"],
    genre="Cinematic / Ballad",
    song_structure="Verse - Pre-Chorus - Chorus - Verse - Pre-Chorus - Chorus - Bridge - Chorus",
    mood_analysis={"Dramatic": 60, "Sad": 40},
    creative_concept="Two former best mates meet in a quiet diner to clear up rumors.",
)
for name, ok in {
    "goal paragraph": "THE GOAL" in p,
    "standalone test": "Standalone test" in p,
    "mates removed from story": "best mates" not in p,
    "no leftover braces": "{" not in p and "None" not in p,
}.items():
    print(("OK   " if ok else "FAIL ") + name)
