"""
constants.py — Fixed lists and configurations for Audingo Songs Forge.
"""

# Fixed list of music genres — curated for educational songwriting where
# vocal clarity is paramount. Every genre here guarantees upfront, clear vocals.
GENRES = [
    "Pop",
    "K-Pop Style (Clear English Vocals)",
    "Synth-Pop / 80s Retro",
    "Indie Pop",
    "Acoustic / Folk",
    "R&B / Contemporary Soul",
    "Country / Americana",
    "Funk / Disco Groove",
    "Reggae / Tropical Pop",
    "Jazz / Bossa Nova",
    "Cinematic / Ballad",
    "Lo-Fi / Chillhop",
    "Melodic Chill Electronic"
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
    "models/gemini-3.6-flash",
    "models/gemini-3.5-flash-lite",
    "models/gemini-flash-latest",
    "models/gemini-flash-lite-latest",
    "models/gemini-3.7-flash",
    "models/gemini-3.1-flash-lite",
]

# 4 Core NGSL Vocabulary Domains
DOMAINS = [
    "Street & Daily Life",
    "Emotions & Relationships",
    "Business & Career",
    "Society, Law & Deep Ideas"
]

DOMAIN_CONFIG = {
    "Street & Daily Life": {
        "emoji": "🏙️",
        "color": "#10B981",
        "bg": "rgba(16, 185, 129, 0.15)",
        "border": "rgba(52, 211, 153, 0.4)",
        "label_ar": "الشارع واليوميات"
    },
    "Emotions & Relationships": {
        "emoji": "❤️",
        "color": "#F43F5E",
        "bg": "rgba(244, 63, 94, 0.15)",
        "border": "rgba(251, 113, 133, 0.4)",
        "label_ar": "المشاعر والقلب"
    },
    "Business & Career": {
        "emoji": "💼",
        "color": "#3B82F6",
        "bg": "rgba(59, 130, 246, 0.15)",
        "border": "rgba(96, 165, 250, 0.4)",
        "label_ar": "العمل والبيزنس"
    },
    "Society, Law & Deep Ideas": {
        "emoji": "🏛️",
        "color": "#8B5CF6",
        "bg": "rgba(139, 92, 246, 0.15)",
        "border": "rgba(167, 139, 250, 0.4)",
        "label_ar": "المجتمع والقانون والفكر"
    }
}


