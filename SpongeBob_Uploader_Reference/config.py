"""
config.py — Central configuration file.

All constants, paths, and tunable settings live here so that every
other module imports from a single source of truth.
"""

from pathlib import Path

# ─── Base Paths ────────────────────────────────────────────────────────────────
BASE_DIR           = Path(__file__).parent.resolve()
UPLOAD_QUEUE_DIR   = BASE_DIR / "Upload_Queue"
UPLOADED_DONE_DIR  = BASE_DIR / "Uploaded_Done"
LOGS_DIR           = BASE_DIR / "logs"
UPLOAD_STATE_FILE  = BASE_DIR / "upload_state.json"
SCHEDULE_TRACKER_FILE = BASE_DIR / "schedule_tracker.json"

# ─── Language Order (also the processing order per episode) ───────────────────
LANGUAGES = ["AR", "EN", "PT", "ES"]

# ─── Show Identity (used by Gemini for character/show-specific tagging) ────────
SHOW_NAME = "SpongeBob SquarePants"

VIDEO_TAGS: dict[str, list[str]] = {
    "EN": ["spongebob recap", "spongebob shorts", "absurd dubs", "spongebob shitpost", "bikini bottom parody", "spongebob voiceover meme", "cartoon recap", "dank spongebob memes", "cursed spongebob", "spongebob gen z humor", "ytp spongebob"],
    "ES": ["resumen bob esponja", "bob esponja shorts", "bob esponja parodia", "doblaje absurdo", "bob esponja shitpost", "ytph bob esponja", "resumen de caricaturas", "momos de bob esponja", "bob esponja turbio", "humor absurdo"],
    "PT": ["resumo bob esponja", "bob esponja shorts", "paródia bob esponja", "dublagem absurda", "bob esponja shitpost", "ytpbr bob esponja", "resumo de desenho", "memes do bob esponja", "bob esponja bizarro", "bob esponja zoeira"],
    "AR": ["تلخيص سبونج بوب", "شورتس سبونج بوب", "دبلجة ساخرة", "عبث مدبلج", "شيت بوست مصري", "ميمز سبونج بوب", "تلخيص كرتون", "شيت بوست كرتون", "سبونج بوب شيت بوست", "abas modablag"]
}

HASHTAGS: dict[str, str] = {
    "EN": "#Shorts #SpongeBob #CartoonRecap #AbsurdDubs",
    "ES": "#Shorts #BobEsponja #Resumen #Parodia",
    "PT": "#Shorts #BobEsponja #Resumo #Parodia",
    "AR": "#Shorts #سبونج_بوب #تلخيص_كرتون #دبلجة_ساخرة"
}

DISCLAIMERS: dict[str, str] = {
    "EN": "This video is a satirical recap and comedic dub intended for mature audiences. The script and storyline have been creatively altered for parody and entertainment purposes.",
    "ES": "Este video es un resumen satírico y un doblaje cómico dirigido a jóvenes y adultos. El guion ha sido alterado creativamente con fines de parodia y entretenimiento.",
    "PT": "Este vídeo é um resumo satírico e uma dublagem cômica voltada para jovens e adultos. O roteiro foi alterado criativamente para fins de paródia e entretenimento.",
    "AR": "هذا الفيديو عبارة عن تلخيص ساخر ودبلجة كوميدية تم إعادة كتابتها بالكامل، موجه للشباب ومحبي الكوميديا. جميع المقاطع تندرج تحت الاستخدام العادل بغرض الترفيه."
}

# ─── Chrome Profile Mapping ────────────────────────────────────────────────────
CHROME_USER_DATA_DIR = str(BASE_DIR / "ChromeProfiles")
CHROME_PROFILES: dict[str, str] = {
    "AR": "Profile_AR",
    "EN": "Profile_EN",
    "ES": "Profile_ES",
    "PT": "Profile_PT",
}

# ─── Scheduling — Egypt Timezone (EET / UTC+2 year-round) ─────────────────────
EGYPT_TIMEZONE = "Africa/Cairo"

# "Two Trains" peak upload times per language (24-hour clock, Egypt local time).
# Each language has exactly two daily slots: Train 1 (afternoon) and Train 2 (evening).
# The scheduler always tries Train 1 first, then Train 2, before moving to the next day.
PEAK_TIMES: dict[str, list[dict[str, int]]] = {
    "AR": [{"hour": 14, "minute":  0}, {"hour": 19, "minute":  0}],
    "EN": [{"hour": 16, "minute":  0}, {"hour": 22, "minute":  0}],
    "PT": [{"hour": 18, "minute":  0}, {"hour": 23, "minute":  0}],
    "ES": [{"hour": 19, "minute":  0}, {"hour": 23, "minute": 50}],
}

MAX_UPLOADS_PER_LANG_PER_DAY = 2

# ─── Gemini API ────────────────────────────────────────────────────────────────
GEMINI_MODEL     = "models/gemini-3.1-flash-lite-preview"
# GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_RPM_SLEEP = 15   # seconds to sleep BETWEEN sequential language API calls

# Language-specific prompt context sent to Gemini
LANGUAGE_CONTEXTS: dict[str, dict] = {
    "AR": {
        "language_name":   "Arabic",
        "language_native": "العربية",
        "audience":        "Arabic-speaking audiences — use Modern Standard Arabic (فصحى) for titles; Egyptian dialect flavour is acceptable in descriptions",
        "tone":            "dramatic, emotional, curiosity-inducing",
        "channel_note":    "This is an Arabic YouTube Shorts recap/drama channel.",
    },
    "EN": {
        "language_name":   "English",
        "language_native": "English",
        "audience":        "Global English-speaking audiences with basic to intermediate comprehension — keep language simple and universally accessible",
        "tone":            "punchy, energetic, globally relatable",
        "channel_note":    "This is a global English YouTube Shorts recap/drama channel.",
    },
    "ES": {
        "language_name":   "Spanish (LATAM)",
        "language_native": "Español (Latinoamérica)",
        "audience":        "Latin American Spanish-speaking audiences",
        "tone":            "energetic, dramatic, emotionally engaging — use LATAM vocabulary and expressions, not Castilian Spanish",
        "channel_note":    "This is a Spanish LATAM YouTube Shorts recap/drama channel.",
    },
    "PT": {
        "language_name":   "Portuguese (Brazil)",
        "language_native": "Português (Brasil)",
        "audience":        "Brazilian Portuguese-speaking audiences",
        "tone":            "exciting, informal, high-energy — use Brazilian Portuguese (pt-BR) vocabulary",
        "channel_note":    "This is a Brazilian Portuguese YouTube Shorts recap/drama channel.",
    },
}

# ─── Playwright / Browser Settings ────────────────────────────────────────────
BROWSER_SLOW_MO_MS    = 50     # global slow-motion for all Playwright actions (ms)
NAV_TIMEOUT_MS        = 60_000  # page navigation timeout
UPLOAD_TIMEOUT_MS     = 300_000 # max wait for "upload complete" indicator (5 min)
SELECTOR_TIMEOUT_MS   = 30_000  # general element wait timeout

BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-notifications",
    "--start-maximized",
    "--no-first-run",
    "--no-default-browser-check",
]

# ─── Retry Settings ───────────────────────────────────────────────────────────
UPLOAD_RETRY_COOLDOWN_SEC = 30  # seconds to wait before the single auto-retry
