"""
constants.py — Fixed lists and configurations for Audingo Songs Forge.
"""

# Fixed list of music genres (closed list for Gemini recommendation and Master Prompt)
GENRES = [
    "Pop",
    "Synth-Pop / 80s Retro",
    "Indie Pop / Dream Pop",
    "Rock",
    "Alternative Rock",
    "Acoustic / Folk",
    "R&B / Contemporary Soul",
    "Hip-Hop / Chillhop",
    "Electronic / EDM / Dance",
    "Country / Americana",
    "Funk / Disco Groove",
    "Reggae / Tropical Pop",
    "Jazz / Bossa Nova",
    "Cinematic / Ballad",
    "Lo-Fi Bedroom Pop"
]

# Fixed list of song structures
SONG_STRUCTURES = [
    "Verse - Chorus - Verse - Chorus - Bridge - Chorus - Outro",
    "Verse - Pre-Chorus - Chorus - Verse - Pre-Chorus - Chorus - Bridge - Chorus",
    "Intro - Verse - Chorus - Verse - Chorus - Outro",
    "AABA (Verse - Verse - Bridge - Verse)",
    "Verse - Chorus - Verse - Chorus - Chorus",
    "Through-Composed (Story-driven, no repeating chorus)"
]

# Mood and sentiment categories
MOOD_CATEGORIES = [
    "Happy",
    "Energetic",
    "Uplifting / Inspiring",
    "Romantic / Sweet",
    "Chill / Relaxed",
    "Nostalgic / Melancholic",
    "Sad / Heartbroken",
    "Dark / Moody",
    "Dramatic / Intense",
    "Playful / Quirky"
]

# Supported Gemini models in priority order as requested:
# Priority 1: Gemini 3 Flash / 2.5 Flash / 2.0 Flash (depending on exact API model naming)
# Priority 2: Gemini 3.5 Flash Lite / 2.5 Flash Lite
# Priority 3: Gemini 3.1 Flash Lite Preview
GEMINI_MODEL_CANDIDATES = [
    "models/gemini-3-flash-preview",      # Choice 1: Gemini 3 Flash
    "models/gemini-3.5-flash-lite",       # Choice 2: Gemini 3.5 Flash Lite
    "models/gemini-3.1-flash-lite-preview", # Choice 3: Gemini 3.1 Flash Lite
    "models/gemini-3.1-flash-lite",
    "models/gemini-2.5-flash",
    "models/gemini-2.5-flash-lite",
]

