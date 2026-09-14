"""
prompt_builder.py — Constructs the Master Prompt for external LLMs (Claude, GPT-4o)
to generate song lyrics, title, and Suno AI music style prompts.

This prompt is heavily optimized for ESL pedagogy: every line must be a natural,
practical, conversational phrase that learners can internalize. No poetic fluff.
"""

from typing import List, Dict, Any, Optional


# Curated keyword presets for Suno v3/v3.5 — strictly under 120 characters,
# guaranteed tempo, clear upfront vocals, and genre-defining acoustic/electronic elements.
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
    """
    Build a concise, keyword-rich Suno style prompt strictly under 120 chars,
    tailored to the selected genre and vocalist.
    """
    voc_str = vocalist.lower().strip()
    if voc_str == "instrumental":
        voc_label = "instrumental, no"
    else:
        voc_label = f"{voc_str}"

    template = SUNO_GENRE_PRESETS.get(
        genre,
        "{genre}, steady 112 bpm, clear upfront {voc} vocals, melodic instruments, clean mix"
    )
    prompt = template.format(voc=voc_label, genre=genre)
    # Strict 120 character cap
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
    Follows the upgraded ESL-optimized songwriting methodology with Internal Quality Gate,
    strict Chorus rules, and Suno audio clarity directives.
    """
    words_list_formatted = "\n".join(f"- **{w}**" for w in target_words)

    # Sort moods by percentage desc and format as a profile string
    mood_items = sorted(
        mood_analysis.items(),
        key=lambda item: item[1] if isinstance(item[1], (int, float)) else 0,
        reverse=True
    )
    mood_str = ", ".join(f"{k}: {v}%" for k, v in mood_items if v > 0)

    # Build the concept line — use Gemini's concept if available, else a safe default
    concept_text = creative_concept if creative_concept else (
        "A vibrant, relatable real-life narrative about real people navigating daily "
        "life, relationships, social moments, and personal goals with authenticity and warmth."
    )

    # Build optional avoidance section for previously used vocabulary
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

### 🎤 CRITICAL SONGWRITING RULES (RHYME, METER & STREET SMALL-TALK):

1. **STRICT RHYME SCHEME (AABB or ABAB) — NO PROSE, NO FREE VERSE:**
   - Every single section ([Verse], [Chorus], [Bridge], [Outro]) MUST have a clear, pleasant, and natural end-rhyme scheme (AABB or ABAB).
   - Rhyme effortlessly with common, everyday words (e.g., *night / light, car / far, street / meet, head / bed, door / floor, say / way, town / down, dust / must, clear / year, phone / alone*).
   - NEVER write unrhymed, blank prose sentences. A song MUST sing and rhyme!

2. **RHYTHMIC METER & LINE LENGTH (6 to 9 Words / 8 to 11 Syllables Per Line):**
   - Song lines must fit a natural musical beat!
   - STRICT LIMIT: Keep lines concise (typically 6 to 9 words, or 8 to 11 syllables).
   - NEVER write long, run-on prose sentences (e.g., do NOT write: *"Saw the job ad online three weeks ago, some global company, didn't think twice"* — that is prose, not a song!). Break thoughts into punchy, rhythmic, rhymed song lines that breathe with the music.

3. **AUTHENTIC STREET SMALL-TALK (100% Conversational, 0% Corporate/Academic):**
   - Write like a real person talking to a close friend over coffee or on a late-night drive.
   - Use natural conversational idioms and phrasal verbs: *grab my keys, hit the road, call it a day, out of the blue, brush it off, no big deal, hang in there, take it easy, back on my feet, running late, figure it out*.
   - **STRICTLY FORBIDDEN:** Academic, clinical, essay, or corporate jargon (e.g., NEVER use phrases like: *"honest assessment"*, *"situate"*, *"complexity"*, *"the latter"*, *"detect"*, *"necessity more than choice"*, *"felt like an investment"*, *"launch a chapter"*). Talk like everyday life, NOT an HR performance review!

4. **EARWORM CHORUS:**
   - The Chorus is the most memorable part of the song. Make it catchy, punchy, rhymed, and relatable, with a memorable hook that people can't stop singing.

---

### 🎚️ Suno Audio & Clarity Instructions:
- **BPM Limit:** Strict mid-tempo range between **110 to 118 BPM** to ensure a relaxed rhythm where words can be articulated naturally.
- **Vocal Production Directives:** Explicitly format the Suno style prompt to prioritize upfront, clear, warm, and conversational vocals with a clean mix.

---

### 📝 Generation Instructions:
1. **Title:** Propose a catchy, down-to-earth song title related to everyday life or personal growth.
2. **Suno Style Prompt (under 120 chars):** Provide a dense, keyword-rich Suno prompt optimized for clarity and a modern vibe (e.g., `Indie pop, 114 bpm, warm clear male vocals, acoustic rhythm, catchy chorus, clean mix`).
3. **Internal Quality Gate (The Earworm & Rhyme Test):**
   - Before outputting, sing each line internally to an acoustic/pop beat.
   - Does every line rhyme naturally in an AABB or ABAB pattern?
   - Is every line short, punchy, and singable (6-9 words)?
   - Does it sound like authentic, street-level spoken English?
   - If any line sounds like a textbook, corporate memo, or unrhymed prose, rewrite it immediately!
4. **Full Lyrics:**
   - Follow the structure: `{song_structure}`.
   - Label each section clearly: `[Verse 1]`, `[Chorus]`, `[Verse 2]`, `[Bridge]`, `[Outro]`, etc.
   - **Bold** every target word when it appears in the lyrics so it is easy to verify (e.g. **{target_words[0] if target_words else "word"}**).
   - Ensure the song tells a vivid, authentic real-life story that learners will love to sing along with!
"""
    return prompt
