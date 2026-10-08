"""
constants.py — Fixed lists and configurations for Audingo Songs Forge.
"""

import logging
logger = logging.getLogger(__name__)

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

# 6 Core NGSL Vocabulary Domains (COCA Frequency Based)
DOMAINS = [
    "Basic / Neutral",
    "Science, Tech & Academia",
    "Emotions & Relationships",
    "Street & Daily Life",
    "Law, Politics & Society",
    "Business & Career"
]

DOMAIN_CONFIG = {
    "Basic / Neutral": {
        "emoji": "🃏",
        "color": "#855600",
        "bg": "rgba(245, 158, 11, 0.15)",
        "border": "rgba(245, 158, 11, 0.4)",
        "label_ar": "الجوكر (كلمات عامة وأساسية)"
    },
    "Science, Tech & Academia": {
        "emoji": "🔬",
        "color": "#006B80",
        "bg": "rgba(6, 182, 212, 0.15)",
        "border": "rgba(6, 182, 212, 0.4)",
        "label_ar": "العلوم والتقنية والأكاديميا"
    },
    "Emotions & Relationships": {
        "emoji": "❤️",
        "color": "#AF3150",
        "bg": "rgba(244, 63, 94, 0.15)",
        "border": "rgba(251, 113, 133, 0.4)",
        "label_ar": "المشاعر والروايات"
    },
    "Street & Daily Life": {
        "emoji": "🏙️",
        "color": "#216E39",
        "bg": "rgba(16, 185, 129, 0.15)",
        "border": "rgba(52, 211, 153, 0.4)",
        "label_ar": "الشارع واليوميات"
    },
    "Law, Politics & Society": {
        "emoji": "🏛️",
        "color": "#7352A2",
        "bg": "rgba(139, 92, 246, 0.15)",
        "border": "rgba(167, 139, 250, 0.4)",
        "label_ar": "القانون والسياسة والمجتمع"
    },
    "Business & Career": {
        "emoji": "💼",
        "color": "#0066CC",
        "bg": "rgba(59, 130, 246, 0.15)",
        "border": "rgba(96, 165, 250, 0.4)",
        "label_ar": "العمل والبيزنس"
    }
}

# --- Category Profiles for Prompts & Critics ---

CASUAL = "casual spoken English, the way people talk to friends and family"

FIELD = (
    "natural spoken English as real people use it in that field (meetings, labs, courts, newsrooms): "
    "plain words, contractions are normal, technical terms only when real speakers say them. "
    "Never textbook, dictionary or document-style sentences"
)

CATEGORY_PROFILES = {
    "Basic / Neutral": {
        "setting": "any ordinary situation that fits the words",
        "register": CASUAL,
        "default_story": "A relatable everyday story grounded in real conversation between real people.",
        "critic_name": "🃏 General Critic",
    },
    "Science, Tech & Academia": {
        "setting": "lab, classroom, study group, tech team, research project",
        "register": FIELD,
        "default_story": "A relatable story set in a lab, classroom, or tech team facing a real challenge together.",
        "critic_name": "🔬 Science & Tech Critic",
    },
    "Emotions & Relationships": {
        "setting": "a real moment between family, friends, or partners",
        "register": CASUAL,
        "default_story": "A heartfelt story about two people working through a real emotional moment.",
        "critic_name": "❤️ Emotions Critic",
    },
    "Street & Daily Life": {
        "setting": "streets, neighborhoods, errands, friends hanging out",
        "register": CASUAL,
        "default_story": "A relatable real-life story about people handling daily life and social moments.",
        "critic_name": "🏙️ Street Life Critic",
    },
    "Law, Politics & Society": {
        "setting": "town hall, courtroom, election night, community meeting, news conversation",
        "register": FIELD + ". Keep any sensitive topic factual and non-graphic",
        "default_story": "A grounded story at a community meeting, courtroom, or civic event where real people debate or decide.",
        "critic_name": "🏛️ Civic & Law Critic",
    },
    "Business & Career": {
        "setting": "office, meeting, interview, negotiation, first day at work",
        "register": FIELD,
        "default_story": "A realistic story in a workplace where people handle work challenges and relationships.",
        "critic_name": "💼 Business Critic",
    },
}

def get_category_profile(domain: str) -> dict:
    if domain not in CATEGORY_PROFILES and domain != "All Domains":
        logger.warning("Unknown domain '%s' passed to get_category_profile; falling back to 'Basic / Neutral'.", domain)
    return CATEGORY_PROFILES.get(domain, CATEGORY_PROFILES["Basic / Neutral"])

# Startup verification to guarantee all UI domains map to a profile
_missing = set(DOMAINS) - set(CATEGORY_PROFILES)
assert not _missing, f"Missing category profiles for DOMAINS: {_missing}"
