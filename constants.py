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
        "color": "var(--studio-amber)",
        "bg": "rgba(245, 158, 11, 0.15)",
        "border": "rgba(245, 158, 11, 0.4)",
        "label_ar": "الجوكر (كلمات عامة وأساسية)"
    },
    "Science, Tech & Academia": {
        "emoji": "🔬",
        "color": "var(--studio-teal)",
        "bg": "rgba(6, 182, 212, 0.15)",
        "border": "rgba(6, 182, 212, 0.4)",
        "label_ar": "العلوم والتقنية والأكاديميا"
    },
    "Emotions & Relationships": {
        "emoji": "❤️",
        "color": "var(--studio-pink)",
        "bg": "rgba(244, 63, 94, 0.15)",
        "border": "rgba(251, 113, 133, 0.4)",
        "label_ar": "المشاعر والروايات"
    },
    "Street & Daily Life": {
        "emoji": "🏙️",
        "color": "var(--studio-green)",
        "bg": "rgba(16, 185, 129, 0.15)",
        "border": "rgba(52, 211, 153, 0.4)",
        "label_ar": "الشارع واليوميات"
    },
    "Law, Politics & Society": {
        "emoji": "🏛️",
        "color": "var(--studio-purple)",
        "bg": "rgba(139, 92, 246, 0.15)",
        "border": "rgba(167, 139, 250, 0.4)",
        "label_ar": "القانون والسياسة والمجتمع"
    },
    "Business & Career": {
        "emoji": "💼",
        "color": "var(--studio-blue)",
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
        "story_settings_examples": [
            "Everyday home, neighborhood, or shared social setting",
            "A casual coffee break, walk, or phone call between close friends",
            "A family gathering or roommates handling everyday tasks together",
            "Kitchen table on a Sunday evening planning a weekly budget or sorting through old receipts",
            "Neighborhood driveway or garage on a Saturday morning fixing a sputtering lawnmower or car with a neighbor",
            "Subway platform or delayed commuter train where two travelers or coworkers share an unexpected honest conversation",
            "Hardware store aisle or home workshop trying to figure out the right tools for a DIY weekend repair",
            "Laundromat late at night waiting for the spin cycle while trading stories about work and family",
            "Local park bench, community garden plot, or dog-walking trail meeting a neighbor at dusk",
            "Supermarket checkout line or grocery parking lot dealing with a runaway cart, spilled groceries, or a forgotten wallet",
            "Moving day living room surrounded by taped cardboard boxes, deciding what to keep and what to give away",
            "Front porch or apartment balcony at sunset sharing leftover takeout while unwinding after a tough week",
            "Rainy roadside or 24-hour gas station waiting out a sudden summer downpour while grabbing coffee",
        ],
        "story_conflict_archetypes": [
            "A relatable personal dilemma, decision, or shared moment between friends or family",
            "Overcoming a daily obstacle through mutual support and clear communication",
            "Two friends resolving an awkward miscommunication over loaned money or an unkept promise with honest, clear words",
            "Roommates or partners negotiating domestic chores and personal space without turning it into an argument",
            "A neighbor offering unexpected hands-on help when another is overwhelmed by a sudden household breakdown",
            "Two siblings going through inherited family items in the attic, balancing nostalgia against practical decluttering",
            "A person wrestling with whether to take a modest life risk (moving, changing routine) and seeking a trusted friend's candid advice",
            "Overcoming unexpected daily frustration (bad weather, flat tire, missed bus) by laughing it off and teaming up to fix it",
        ],
        "domain_directive": (
            "Use clear, natural spoken English suitable for everyday life. "
            "Prioritize conversational dialogue that any native speaker would say to a friend. "
            "Because these words are universal, foundational everyday terms, integrate them actively into characters' dialogue, questions, and reactions. "
            "INVENT, DO NOT COPY: The setting and conflict examples are structural springboards, never a fixed menu to copy mechanically. "
            "Observe the underlying human patterns and invent a fresh, original real-life scenario tailored uniquely to the given words."
        ),
    },
    "Science, Tech & Academia": {
        "setting": "lab, classroom, study group, tech team, research project",
        "register": FIELD,
        "critic_guidance": (
            "Accept moderately formal, educated spoken English in this category; street slang is not the standard. "
            "Judge the actual story, including personal or family scenes involving academic or technical lives; "
            "the suggested settings are examples, not mandatory locations. "
            "Do not deduct merely because storage, assumption, connect, scientist, university, input, database, "
            "necessary, analysis, or progress sounds academic, technical, or professional. "
            "For example, 'These boxes sat in storage for years.', 'I made a bad assumption.', "
            "'He taught at the university.', 'He always wanted my input,' and 'Not everything needs analysis.' "
            "can be natural in a family reflection. These are calibration examples, not guaranteed scores. "
            "Technical vocabulary does not inherently break an emotional mood. "
            "Still flag a genuinely wrong meaning, unnatural collocation, unclear reference, or unsupported story jump; "
            "explain the specific problem rather than calling a word formal, clinical, or corporate."
        ),
        "default_story": "A relatable story set in a lab, classroom, or tech team facing a real challenge together.",
        "critic_name": "🔬 Science & Tech Critic",
        "story_settings_examples": [
            "University research laboratory or science facility working late before a grant or paper submission deadline",
            "Tech startup, IT office, or software engineering team troubleshooting a critical system crash or bug before launch",
            "Engineering workshop, garage, or robotics bench testing an experimental hardware prototype under pressure",
            "Medical clinic, diagnostic lab, or clinical study reviewing complex patient data or trial outcomes",
            "College campus study room or library where graduate students prepare for a high-stakes capstone defense or exam",
        ],
        "story_conflict_archetypes": [
            "Two researchers racing the clock when test results vary wildly hours before their project deadline",
            "A software engineer and team lead debating whether to rewrite core logic or push a quick patch",
            "A specialist and an apprentice discovering an unexpected flaw in their original assumptions and finding a fix",
            "Colleagues pushing through exhaustion, pooling their knowledge, and celebrating a hard-won discovery",
        ],
        "domain_directive": (
            "Accept educated, professional spoken English (collegiate, tech, lab, or clinical dialogue); street slang is NOT the standard. "
            "Anchor target words in active spoken dialogue between collaborators (e.g. 'demonstrate the fix', 'we need a specialist', "
            "'the error is constant', 'results vary between tests', 'don't be too critical', 'describe what failed', 'that occupies my time'). "
            "Do NOT drop academic or technical words simply because they sound educated; native speakers use them constantly in these settings."
        ),
    },
    "Emotions & Relationships": {
        "setting": "a real moment between family, friends, or partners",
        "register": CASUAL,
        "default_story": "A heartfelt story about two people working through a real emotional moment.",
        "critic_name": "❤️ Emotions Critic",
        "story_settings_examples": [
            "Quiet kitchen table or late-night coffee shop where partners talk through an unspoken truth",
            "Airport departure gate, bus depot, or train platform before an extended separation",
            "Long drive at dusk or quiet porch where old friends address a past misunderstanding",
            "Backyard family reunion or quiet bedside conversation during recovery",
        ],
        "story_conflict_archetypes": [
            "Overcoming fear of vulnerability to confess honest feelings and reconcile",
            "Two close friends working through distance and changing life priorities without losing their bond",
            "Reassuring a partner or family member through grief, uncertainty, or personal transition",
        ],
        "domain_directive": (
            "Focus on emotionally authentic, heartfelt spoken English. Keep dialogue tender, vulnerable, and grounded in real human connection."
        ),
    },
    "Street & Daily Life": {
        "setting": "streets, neighborhoods, errands, friends hanging out",
        "register": CASUAL,
        "default_story": "A relatable real-life story about people handling daily life and social moments.",
        "critic_name": "🏙️ Street Life Critic",
        "story_settings_examples": [
            "Neighborhood diner counter, auto repair shop, or laundromat on a busy Saturday morning",
            "Subway platform, crowded bus stop, or city sidewalk during the evening rush",
            "Corner grocery store, barber shop, or street market where locals chat and trade news",
            "Apartment stoop or block party where neighbors deal with daily neighborhood drama",
        ],
        "story_conflict_archetypes": [
            "An unexpected car breakdown, missed bus, or lost keys sparking cooperative problem-solving",
            "Navigating rent pressure, tight budgets, and honest everyday hustle with warmth and humor",
            "A spontaneous act of neighborhood kindness turning a stressful day around",
        ],
        "domain_directive": (
            "Use authentic everyday colloquial American English. Keep situations energetic, grounded, and relatable, with zero explicit profanity."
        ),
    },
    "Law, Politics & Society": {
        "setting": "town hall, courtroom, election night, community meeting, news conversation",
        "register": FIELD + ". Keep any sensitive topic factual and non-graphic",
        "default_story": "A grounded story at a community meeting, courtroom, or civic event where real people debate or decide.",
        "critic_name": "🏛️ Civic & Law Critic",
        "story_settings_examples": [
            "Courthouse corridor, legal clinic, or consultation room preparing for a crucial hearing",
            "Town hall, municipal council room, or school auditorium during a heated public forum",
            "Community center or grassroots organizing office counting petition signatures late at night",
            "Neighborhood assembly debating a local zoning, environment, or public safety resolution",
        ],
        "story_conflict_archetypes": [
            "A legal advocate and an ordinary citizen standing firm against an unjust policy",
            "Neighbors with opposing political opinions finding common ground on a shared community challenge",
            "Uncovering vital public records or testimony that shifts the entire debate before a final vote",
        ],
        "domain_directive": (
            "Use articulate civic and spoken conversational English. Keep sensitive topics factual and grounded in everyday human rights, community responsibility, and fair process."
        ),
    },
    "Business & Career": {
        "setting": "office, meeting, interview, negotiation, first day at work",
        "register": FIELD,
        "default_story": "A realistic story in a workplace where people handle work challenges and relationships.",
        "critic_name": "💼 Business Critic",
        "story_settings_examples": [
            "Glass conference room or executive office closing a high-stakes partnership or contract",
            "Waiting area or interview room before a career-defining job interview or performance review",
            "Busy warehouse, restaurant floor, or retail stockroom handling an urgent supply deadline",
            "Late-night office desk where co-founders balance financial reality with company vision",
        ],
        "story_conflict_archetypes": [
            "An employee advocating for their worth and team compensation using clear operational evidence",
            "Two colleagues resolving a tactical disagreement while maintaining mutual professional respect",
            "A team racing to meet a client milestone after a major vendor default",
        ],
        "domain_directive": (
            "Use conversational workplace English. Target words fit natural professional dialogue, team coordination, negotiation, and career milestones."
        ),
    },
}

def get_category_profile(domain: str) -> dict:
    if domain not in CATEGORY_PROFILES and domain != "All Domains":
        logger.warning("Unknown domain '%s' passed to get_category_profile; falling back to 'Basic / Neutral'.", domain)
    return CATEGORY_PROFILES.get(domain, CATEGORY_PROFILES["Basic / Neutral"])

# Startup verification to guarantee all UI domains map to a profile
_missing = set(DOMAINS) - set(CATEGORY_PROFILES)
assert not _missing, f"Missing category profiles for DOMAINS: {_missing}"
