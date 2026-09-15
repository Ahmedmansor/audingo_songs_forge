"""
prompt_service.py — Constructs Suno AI style prompts and Master Prompts for external LLMs.
"""

from typing import List, Dict, Any, Optional

SUNO_GENRE_PRESETS = {
    "Pop": "Pop, steady 116 bpm, clear upfront {voc} vocals, bright acoustic guitar, modern synth, clean punchy mix",
    "K-Pop Style (Clear English Vocals)": "K-Pop, steady 118 bpm, clear upfront {voc} vocals, punchy synth bass, crisp percussion, clean modern mix",
    "Synth-Pop / 80s Retro": "Synthwave, 80s synth-pop, steady 112 bpm, clear upfront {voc} vocals, warm analog synths, pulsing bass, clean mix",
    "Indie Pop": "Indie pop, steady 114 bpm, clear upfront {voc} vocals, warm acoustic guitar, melodic bassline, clean airy mix",
    "Acoustic / Folk": "Acoustic folk, steady 110 bpm, clear upfront {voc} vocals, acoustic guitar, subtle strings, clean natural mix",
    "R&B / Contemporary Soul": "Contemporary R&B, soul groove, steady 110 bpm, clear upfront {voc} vocals, electric piano, warm bass, clean mix",
    "Country / Americana": "Americana, modern country, steady 112 bpm, clear upfront {voc} vocals, acoustic strumming, pedal steel, clean mix",
    "Funk / Disco Groove": "Disco funk groove, steady 116 bpm, clear upfront {voc} vocals, rhythmic bassline, clean electric guitar, clean mix",
    "Reggae / Tropical Pop": "Tropical reggae pop, steady 110 bpm, clear upfront {voc} vocals, island guitar skank, warm bass, clean mix",
    "Jazz / Bossa Nova": "Bossa nova, smooth jazz, steady 110 bpm, clear upfront {voc} vocals, nylon acoustic guitar, upright bass, clean mix",
    "Cinematic / Ballad": "Cinematic ballad, steady 110 bpm, clear upfront {voc} vocals, emotive grand piano, lush strings, clean dynamic mix",
    "Lo-Fi / Chillhop": "Lo-fi chillhop, steady 110 bpm, clear upfront {voc} vocals, mellow electric piano, relaxed bass, clean vinyl mix",
    "Melodic Chill Electronic": "Melodic chill electronic, steady 112 bpm, clear upfront {voc} vocals, soft piano, warm ambient pads, clean mix",
}


def build_suno_style_prompt(genre: str, vocalist: str = "Male") -> str:
    """Build concise, keyword-rich Suno style prompt strictly under 120 chars."""
    voc_str = vocalist.lower().strip()
    voc_label = "instrumental, no" if voc_str == "instrumental" else f"{voc_str}"

    template = SUNO_GENRE_PRESETS.get(
        genre,
        "{genre}, steady 112 bpm, clear upfront {voc} vocals, melodic instruments, clean mix"
    )
    prompt = template.format(voc=voc_label, genre=genre)
    if len(prompt) > 120:
        prompt = prompt[:117] + "..."
    return prompt


def generate_master_prompt(
    target_words: List[str],
    genre: str,
    song_structure: str,
    mood_analysis: Dict[str, Any],
    creative_concept: str = "",
    previously_used_words: Optional[List[str]] = None
) -> str:
    """
    Format a complete, production-ready Master Prompt ready to be copied into Claude / GPT-4o.
    Follows ESL-optimized songwriting methodology with Internal Quality Gate,
    strict Chorus rules, and Suno audio clarity directives.
    """
    words_list_formatted = "\n".join(f"- **{w}**" for w in target_words)

    mood_items = sorted(
        mood_analysis.items(),
        key=lambda item: item[1] if isinstance(item[1], (int, float)) else 0,
        reverse=True
    )
    mood_str = ", ".join(f"{k}: {v}%" for k, v in mood_items if v > 0)

    concept_text = creative_concept if creative_concept else (
        "A vibrant, relatable real-life narrative about real people navigating daily "
        "life, relationships, social moments, and personal goals with authenticity and warmth."
    )

    avoidance_section = ""
    if previously_used_words:
        used_words_str = ", ".join(previously_used_words)
        avoidance_section = f"""---

### 🚫 Mindful Vocabulary Diversity (Smart Repetition Avoidance):
- **Previously Covered Thematic Vocabulary to Avoid/Minimize (Where Practical):**
{used_words_str}

- **Core Pedagogy & Goal:** To help the ESL learner discover fresh vocabulary and avoid repetitive themes across songs, make a conscious effort to steer away from the previously covered content words listed above. When drafting lyrics, explore fresh situations, synonyms, or new imagery that introduces diverse vocabulary.
- **CRITICAL SMART GUIDELINES (Conversational Naturalness > Word Avoidance):**
  - This is a **mindful pedagogical guideline**, NOT a rigid, artificial ban.
  - **100% UNCONDITIONAL EXEMPTIONS:** All structural grammar glue, pronouns (*I, you, we, they, me, us*), prepositions (*in, on, at, with, about, for*), conjunctions (*and, but, because, so*), and indispensable everyday conversational verbs and words (*be, have, do, go, get, see, know, think, take, make, come, say, want, look, feel, good, time, way, day, life, friend, home, etc.*) are completely exempt and MUST be used freely to maintain natural English.
  - **GOLDEN RULE:** Conversational realism, emotional authenticity, and musical rhythm ALWAYS take priority. Under NO circumstances should you sacrifice natural phrasing or write awkward, robotic lines just to dodge a previously covered word!

"""

    prompt = f"""# 🎵 MASTER SONGWRITING & SUNO PROMPT (STREET SMALL-TALK & CATCHY RHYMES)

You are a Grammy-winning songwriter and world-class ESL pedagogy specialist who produces modern, radio-ready hits.

Your mission is to write a catchy, highly relatable, and musical song that naturally weaves 20 specific target vocabulary words into authentic, everyday street-level situations (hanging out with friends, relationships, daily errands, moving places, late-night phone calls, road trips, personal struggles), while keeping the lyrics effortless, conversational, and packed with natural rhymes and great rhythmic cadence.

---

### 🎯 Mandatory Target Vocabulary (All 20 words MUST appear):
{words_list_formatted}

*(Note: Inflected forms like plurals, verb tenses, etc. are allowed. You have full permission to use natural derivatives or alter the word class slightly if it prevents awkward phrasing. For example, use "every day" as two words if it fits better than the adjective "everyday", or use a plural/past-tense form if it sounds more natural in context.)*

{avoidance_section}---

### 🎨 Creative Direction & Musical Vibe:
- **Genre & Style:** {genre} (clean, warm, rhythm-driven, and highly relatable)
- **Song Structure:** {song_structure}
- **Emotional Mood Profile:** {mood_str if mood_str else "Casual & Conversational: 70%, Reflective: 30%"}
- **Core Concept / Story:** {concept_text}

---

### ⚡ Critical ESL Songwriting Rules:
1. **Natural Colloquial Phrasing:** The lyrics must sound like modern fluent speech put to melody.
2. **Rhyme & Cadence:** Use crisp, satisfying end-rhymes (AABB, ABAB) with bounce and flow.
3. **No Fluff / Fillers:** Avoid archaic words, awkward inversions, or artificial metaphors.
4. **Pedagogical Anchoring:** Every target word must be embedded in a context where its meaning is instantly graspable.

---

### 📦 REQUIRED OUTPUT FORMAT:
Return the complete song formatted exactly as follows:

[Title]: <Song Title Here>
[Genre]: {genre}
[Suno Style]: {build_suno_style_prompt(genre, 'Male')}

[Lyrics]:
(Include all structural tags: [Verse 1], [Chorus], [Verse 2], [Chorus], [Bridge], [Chorus], [Outro])
"""
    return prompt
