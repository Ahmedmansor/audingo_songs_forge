"""
prompt_service.py — Constructs Suno AI style prompts and Master Prompts for external LLMs.
"""

from typing import List, Dict, Any, Optional
import re

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
    "Cinematic / Ballad": "Cinematic ballad, steady 110 bpm, clear upfront {voc} vocals, emotive grand piano, lush strings, soft intimate verses, building dynamics, powerful chorus, clean dynamic mix",
    "Lo-Fi / Chillhop": "Lo-fi chillhop, steady 110 bpm, clear upfront {voc} vocals, mellow electric piano, relaxed bass, clean vinyl mix",
    "Melodic Chill Electronic": "Melodic chill electronic, steady 112 bpm, clear upfront {voc} vocals, soft piano, warm ambient pads, clean mix",
}


def build_suno_style_prompt(genre: str, vocalist: str = "Male") -> str:
    voc = vocalist.lower().strip()
    template = SUNO_GENRE_PRESETS.get(
        genre,
        "{genre}, steady 112 bpm, clear upfront {voc} vocals, melodic instruments, clean mix",
    )
    if voc == "instrumental":
        template = template.replace("clear upfront {voc} vocals", "instrumental, no vocals")
    prompt = template.format(voc=voc, genre=genre)

    # Trim whole comma-separated items instead of cutting mid-word
    parts = prompt.split(", ")
    while len(", ".join(parts)) > 200 and len(parts) > 1:
        parts.pop()
    return ", ".join(parts)


def _norm(name: str) -> str:
    return name.lower().replace(" ", "").replace("-", "")

def parse_song_structure(structure_str: str) -> str:
    """Parses a structure string like 'Verse - Chorus - Bridge' into output format blocks."""
    s = structure_str.lower()
    if "through-composed" in s or "through composed" in s:
        return "[Verse 1]\n(4-6 lines)\n[Verse 2]\n(4-6 lines)\n[Verse 3]\n(4-6 lines)\n[Verse 4]\n(4-6 lines)"
    if "aaba" in s:
        return "[Verse 1]\n(4-6 lines)\n[Verse 2]\n(same number of lines as Verse 1)\n[Bridge]\n(4-8 lines)\n[Verse 3]\n(same number of lines as Verse 1)"

    # Split on " - ", dashes or arrows, but NOT on the hyphen inside "Pre-Chorus"
    parts = [p.strip() for p in re.split(r"\s+[-–—]\s+|\s*(?:→|->)\s*", structure_str) if p.strip()]

    def is_real_chorus(name: str) -> bool:
        n = _norm(name)
        return "chorus" in n and not n.startswith("pre")

    lines = []
    verse_count = pre_count = chorus_count = 0

    for idx, part in enumerate(parts):
        n = _norm(part)
        if n.startswith("verse"):
            verse_count += 1
            note = "(4-6 lines)" if verse_count == 1 else "(same number of lines as Verse 1)"
            lines.append(f"[Verse {verse_count}]\n{note}")
        elif n.startswith("prechorus"):
            pre_count += 1
            note = "(4 lines)" if pre_count == 1 else "(same as the first Pre-Chorus)"
            lines.append(f"[Pre-Chorus]\n{note}")
        elif "chorus" in n:
            chorus_count += 1
            is_last = not any(is_real_chorus(p) for p in parts[idx + 1:])
            if chorus_count == 1:
                lines.append("[Chorus]\n(4 lines)")
            elif is_last:
                lines.append("[Final Chorus]\n(the Chorus with at most one changed line)")
            else:
                lines.append("[Chorus]\n(identical to the first Chorus)")
        elif "bridge" in n:
            lines.append("[Bridge]\n(4-8 lines)")
        elif "intro" in n:
            lines.append("[Intro]\n(2-4 lines)")
        elif "outro" in n:
            lines.append("[Outro]\n(2-4 lines)")
        else:
            lines.append(f"[{part}]\n(4 lines)")

    return "\n".join(lines)


def generate_master_prompt(
    target_words: List[str],
    genre: str,
    song_structure: str,
    mood_analysis: Dict[str, Any],
    creative_concept: str = "",
    selected_domain: str = "Street & Daily Life",
    vocalist: str = "Male",
    dialect: str = "American English"
) -> str:
    """
    Format a complete, production-ready Master Prompt ready to be copied into Claude / GPT-4o.
    Follows ESL-optimized songwriting methodology.
    """
    words_list_formatted = ", ".join(target_words)

    # Convert mood percentages to a descriptive string as per user instructions
    mood_items = sorted(
        mood_analysis.items(),
        key=lambda item: item[1] if isinstance(item[1], (int, float)) else 0,
        reverse=True
    )
    mood_str = ", ".join(k for k, v in mood_items if isinstance(v, (int, float)) and v > 0)
    if not mood_str:
        mood_str = "Casual, Conversational, Reflective"

    story_text = creative_concept if creative_concept else (
        "A vibrant, relatable real-life narrative about real people navigating daily "
        "life, relationships, social moments, and personal goals with authenticity and warmth."
    )
    if "american" in dialect.lower():
        story_text = re.sub(r"\bmates\b", "friends", story_text, flags=re.I)
        story_text = re.sub(r"\bmate\b", "friend", story_text, flags=re.I)

    suno_style = build_suno_style_prompt(genre, vocalist)

    structure_formatted = parse_song_structure(song_structure)

    chorus_rule = (
        "- Chorus: 4 short lines with one clear hook line. Repeat it identically every time; "
        "the Final Chorus may change one line for progression.\n"
    ) if "[Chorus]" in structure_formatted else ""

    prompt = f"""# SONG DRAFT PROMPT (ESL LEARNING)

Write one original song for an English learner.

THE GOAL: the learner should be able to memorize ANY single line and use it as-is in real life. So every line must be a natural sentence that a native speaker would actually say, and it must still make sense and be useful when read on its own, outside the song.

The song tells one believable everyday story and uses the target words only where they sound natural.

## INPUTS
- Target words: {words_list_formatted}
- Theme: {selected_domain}
- Story: {story_text}
- Genre: {genre}
- Mood: {mood_str}
- Dialect: {dialect}

## PRIORITY ORDER (when rules conflict)
1. Every line sounds natural and is something a real person would say.
2. The story is coherent and in order.
3. Clean rhyme and rhythm.
4. Target words.

## TARGET WORDS
- Try hard to use every target word. Choose story details that give each word a natural place.
- Drop a word only if every possible use would sound forced or unnatural. Never lower line quality to fit a word.
- Use each word in its most common everyday meaning, never in a poetic or abstract sense.
- Inflected forms are fine (plural, tense, "every day").
- Mild words (hell, damn, God) only inside ordinary everyday expressions. No standalone swearing or crude language.
- Sensitive words (kill, terrorist, etc.) only in ordinary or figurative everyday use, otherwise skip.
- If a word belongs to a different dialect (e.g. "mate" when the dialect is American English), adapt it naturally or skip it. Never mix dialects in one song.

## STORY RULES
- Plan the story silently first: setting, characters, 5-6 events in time order, ending, and where each target word fits naturally.
- One place, one continuous situation. Memories are allowed only if they directly support the conflict.
- Every line advances or deepens the story. No random imagery, no jumps outside it.

## LINE QUALITY RULES
- Each line is 6-9 syllables. Verses all have the same number of lines.
- Test every line: would a native speaker say this to a friend? If not, rewrite it.
- No: poetic or abstract metaphors, inverted word order, filler to fit rhyme ("this way", "I'd say", "all along" as padding), stacked clichés.
- If a perfect rhyme forces an awkward line, use a near rhyme or rewrite both lines.
- Prefer direct sentences a learner can reuse in real life.

## CHORUS & SUNO RULES
{chorus_rule}- Write numbers as words. No parentheses, ad-libs, or sound effects inside lyrics.
- Avoid hard-to-pronounce words at the end of lines.

## SELF-CHECK (do silently, then fix before output)
For every line: natural? in story order? right length? dialect consistent? no filler? Is each target word used in its natural everyday meaning, not forced?
Standalone test: if this line is read alone, is it a natural, useful sentence a learner could say in real life?
Rewrite any line that fails.

## OUTPUT FORMAT
Output only the following. Do not print your plan, notes, or explanations.
Text in parentheses below are instructions about line counts. Never print them.

[Title]: ...
[Genre]: {genre}
[Suno Style]: {suno_style}

[Lyrics]:
{structure_formatted}

[Words used]: ...
[Words left out]: ...
"""
    return prompt
