"""
prompt_service.py — Constructs Suno AI style prompts and Master Prompts for external LLMs.
"""

from typing import List, Dict, Any, Optional
import re
from constants import get_category_profile

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


ESL_GOAL_BLOCK = """THE GOAL: the learner should be able to memorize ANY single line and use it as-is in real life.
Every line must be:
- Natural: something native speakers really say. Nothing awkward, inverted or overly poetic.
- One consistent dialect. No mixing of American and British forms.
- Short and easy to memorize.
- Part of ONE story told in order, with no jumps outside the story or setting.
- Clean: no explicit profanity. Mild words (hell, damn, God) only inside ordinary everyday expressions.
- Using target words in their everyday meaning. Never force a word in."""


def build_manual_surgical_prompt(
    lyrics_text: str,
    line_breakdown: List[Dict[str, Any]],
    theme: str = "Basic / Neutral",
    genre: str = "Cinematic / Ballad",
    concept: str = "",
    target_words: Optional[List[str]] = None,
    selected_domain: Optional[str] = None
) -> str:
    """
    Constructs a surgical prompt ready to copy-paste into Claude 3.5 Sonnet / GPT-4o,
    categorizing lines strictly by score: 🟢 >= 90 (Locked), 🟡 75-89 (Optional Polish), 🔴 < 75 (Rewrite Required).
    """
    domain_to_use = selected_domain if selected_domain else theme
    p = get_category_profile(domain_to_use)

    story_concept = concept.strip() if concept else p["default_story"]

    words_list = target_words or []
    words_joined = ", ".join(words_list) if words_list else "None specified"

    # Strict code-based thresholding
    passed_lines = [l for l in line_breakdown if l.get("score", 0) >= 90]
    critical_lines = [l for l in line_breakdown if l.get("score", 0) < 75]
    warning_lines = [l for l in line_breakdown if 75 <= l.get("score", 0) < 90]

    crit_text = "\n".join([f'- Line: "{l.get("line", "")}"\n  Score: {l.get("score", 0)}%\n  Critique: {l.get("comment") or l.get("issue", "")}' for l in critical_lines]) if critical_lines else "None (All lines passed critical checks!)"
    warn_text = "\n".join([f'- Line: "{l.get("line", "")}"\n  Score: {l.get("score", 0)}%\n  Critique: {l.get("comment") or l.get("issue", "")}' for l in warning_lines]) if warning_lines else "None"
    passed_text = "\n".join([f'- "{l.get("line", "")}"' for l in passed_lines]) if passed_lines else "None"

    # Map status by line text
    status_dict = {}
    for l in line_breakdown:
        raw_txt = l.get("line", "").strip().lower()
        score = l.get("score", 0)
        if score >= 90:
            eff = "✅"
        elif score >= 75:
            eff = "⚠️"
        else:
            eff = "❌"
        if raw_txt:
            status_dict[raw_txt] = eff

    annotated_lines = []
    for raw_l in lyrics_text.splitlines():
        cleaned = raw_l.strip().lower().strip(",").strip(".")
        if not raw_l.strip() or raw_l.strip().startswith("["):
            annotated_lines.append(raw_l)
        else:
            match_status = None
            for k, line_status in status_dict.items():
                if k in cleaned or cleaned in k:
                    match_status = line_status
                    break
            if match_status == "❌":
                annotated_lines.append(f"[🚨 REWRITE REQUIRED ❌] {raw_l}")
            elif match_status == "⚠️":
                annotated_lines.append(f"[⚠️ OPTIONAL POLISH] {raw_l}")
            elif match_status == "✅":
                annotated_lines.append(f"[🔒 LOCKED ✅ - DO NOT TOUCH] {raw_l}")
            else:
                annotated_lines.append(f"[⚠️ OPTIONAL POLISH] {raw_l}")
    annotated_lyrics_block = "\n".join(annotated_lines)

    domain_dir = p.get("domain_directive", "")
    domain_guidance_str = f" {domain_dir}" if domain_dir else ""

    return f"""You are an expert English linguist and a professional ESL teacher who edits song lyrics for learners.
Your mission is to perform SURGICAL REPAIRS on the song lyrics below.

{ESL_GOAL_BLOCK}

CRITICAL PEDAGOGICAL MISSION:
This song is an educational song built around a strict list of target vocabulary words.
Every target word that is currently in the lyrics MUST be preserved. Do not add target words that are missing. Dropping or replacing a present target word with a synonym is a critical failure.

CONTEXTUAL ANCHORS:
- Theme: "{domain_to_use}"
- Category guidance: Setting: {p['setting']}. Register: {p['register']}.{domain_guidance_str}
- Musical Genre: "{genre}"
- Core Story / Setting / Concept: "{story_concept}"
- Dialect: American English (never mix dialects; use one consistent variety of English)

🎯 TARGET VOCABULARY (Preserve every target word currently in the lyrics; do not add missing ones):
{words_joined}

🔒 VERIFIED GREEN LINES ({len(passed_lines)} Lines - 100% LOCKED, DO NOT CHANGE):
{passed_text}

🚨 CRITICAL FLAWED LINES (Must be rewritten - Score < 75%):
{crit_text}

⚠️ MINOR WARNING LINES (Only tweak if it improves flow - Score 75-89%):
{warn_text}

---
CURRENT ANNOTATED SONG LYRICS (Follow the tags next to each line):
{annotated_lyrics_block}
---

=== SURGICAL REPAIR INSTRUCTIONS (OVERRIDE ANY CONFLICT ABOVE) ===

A. GREEN LINES (🔒) ARE LOCKED IN THE LYRICS OUTPUT.
   Never delete, reorder, merge, split, or reword them in Part 1. Treat them as fixed anchors. Every green line must appear in the output exactly once per place it appears now, in the same position.

B. EDIT SCOPE: Edit ONLY the ⚠️ (yellow) and ❌ (red) lines. If none are red, do not invent problems. A yellow line may be kept unchanged if no real improvement exists.

C. TARGET WORDS & TONE:
   - Every target word currently in the lyrics must remain intact. Do not add target words that are missing.
   - Do NOT replace any present target word with a synonym.
   - Do NOT add new profanity or crude vulgarities in edited lines. Existing coarse language inside green lines is intentional (street-life realism) and must not be treated as an error.

D. RED LINES FOR EDITED LINES (OVERRIDE ALL GOALS BELOW):
   An edited line must never be awkward, stiff, inverted, poetic, outside the story, an abrupt jump, empty of learning value, or have an unclear speaker. If you cannot fix a line without crossing a red line, keep the original line and say so in the change log. This applies to yellow and red lines only; green lines stay locked.

E. IMPROVEMENT GOALS FOR EDITED LINES (priority order):
   1. THEMATIC CONSISTENCY & SETTING CONTINUITY: Every edited line must stay inside the song's theme ("{domain_to_use}") and established setting / story ("{story_concept}"). Do not introduce new locations, characters, or topics that drift away from the central story. If a line does not serve the core story, rewrite it.
   2. PRACTICAL USABILITY:
      - An ESL learner who memorizes the line should be able to say it naturally in this setting. Prefer natural spoken English over poetic or literary phrasing.
      - Use natural contractions (I'm, don't, can't); avoid stiff forms unless the setting requires formality.
      - Standalone test: read alone, the line must be natural and useful.
   3. NO FORCED RHYME: A line must add real narrative meaning, not exist only to rhyme.
   4. NO REPETITION: Avoid repeating the same opening word or key noun in nearby lines.
   5. FLOW & MELODY: Keep syllable count (±1) and rhyme scheme so the melody still fits.
   6. LENGTH: 6 to 9 syllables per edited line (±1).

F. FINAL SELF-CHECK (execute silently before outputting):
   - Count green lines: none missing, none changed, none repositioned.
   - Verify all present target words are still preserved.
   - Ensure each edited line passes goals 1 to 6 (including Standalone test and 6-9 syllables) and respects all Red Lines.
   - If a yellow line cannot be improved, keep it as is.

G. OUTPUT FORMAT:
   Part 1: The complete clean lyrics (without any [🔒], [🚨], or [⚠️] tags), ready to paste.
   Part 2: Change log, one line per edited line:
   "Original line" → "New line" | Reason for change
   (If nothing was edited, write "No edits needed".)
   
   === REVIEW ===
   Part 3: GREEN LINE REVIEW (suggestions only, NOT applied to Part 1).
   Check the green lines against goals E1 to E6, plus:
   - Flag any green line that breaks thematic consistency or setting continuity.
   - Is the line natural spoken English a learner can reuse in this setting?
   - Is the register (rude, formal, poetic, profane) flagged for the learner?
   - Any unclear "he" or "they", or a fact the speaker could not realistically know in the scene?
   - Is there weak coherence, forced rhyme, or repetition across the whole song?
   - Does any green line clash with an edit made in Part 1?
   Only mention a green line if you have a REAL, specific improvement. Do not pad the list. For each one give:
   "Original → Suggested | reason | priority (high / medium / low)"
   If nothing is worth changing, write "Green lines are solid, no suggestions."
   Finish with a verdict: overall coherence, educational value, and whether the song is ready to publish.

H. NEVER apply Part 3 suggestions to Part 1 unless the user explicitly approves them in the next message."""


def generate_master_prompt(
    target_words: List[str],
    genre: str,
    song_structure: str,
    mood_analysis: Dict[str, Any],
    creative_concept: str = "",
    selected_domain: str = "Basic / Neutral",
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

    p = get_category_profile(selected_domain)

    story_text = creative_concept if creative_concept else p["default_story"]

    suno_style = build_suno_style_prompt(genre, vocalist)

    structure_formatted = parse_song_structure(song_structure)

    chorus_rule = (
        "- Chorus: 4 short lines with one clear hook line. Repeat it identically every time; "
        "the Final Chorus may change one line for progression.\n"
    ) if "[Chorus]" in structure_formatted else ""

    domain_directive = p.get("domain_directive", "")
    domain_guidance_txt = f" {domain_directive}" if domain_directive else ""
    domain_target_rule = f"- Domain-specific guidance: {domain_directive}\n" if domain_directive else ""

    if selected_domain == "Science, Tech & Academia":
        target_words_philosophy = (
            "- HIGH VOCABULARY INTEGRATION BENCHMARK (14 to 17 words): In this technical/academic category, your benchmark is to naturally integrate at least 14 to 17 of the 20 target words into the collaborators' spoken dialogue.\n"
            "- STRICT PROHIBITION AGAINST LAZY SYNONYM REPLACEMENT: Never substitute a target word with a casual, generic synonym! For example, do NOT write 'make sure' when you have 'ensure'; do NOT write 'chance' when you have 'opportunity'; do NOT write 'this place' or 'here' when you have 'laboratory'; do NOT write 'enough' when you have 'sufficient'; do NOT write 'look at' or 'go through' when you have 'evaluate' or 'observe'; do NOT write 'aim' when you have 'objective'; do NOT write 'rules' when you have 'guideline'. Use the exact target words actively and authentically in their professional dialogue.\n"
            "- EDUCATED VOCABULARY IS NOT STIFF: Educated, professional terms in this field are natural spoken English for real researchers/specialists and do NOT violate Red Line 1. Drop a word ONLY as an absolute last resort if it genuinely cannot fit without distorting syntax or breaking the scene. Never drop words merely out of convenience or laziness.\n"
        )
    else:
        target_words_philosophy = (
            "- The words are drawn randomly from a larger database. The goal is NOT to use all of them. The goal is a perfect song: natural lines and a connected story always come before word coverage.\n"
            "- Coverage is tracked across the whole song collection, and a separate verification step counts which target words were used and which extra database words appeared naturally. Do not chase a count.\n"
        )

    prompt = f"""# SONG DRAFT PROMPT (ESL LEARNING)

Write one original song for an English learner.

{ESL_GOAL_BLOCK}

The song tells one believable real-life story that fits the theme and uses the target words only where they sound natural.

## INPUTS
- Target words: {words_list_formatted}
- Theme: {selected_domain}
- Category guidance: Setting: {p['setting']}. Register: {p['register']}.{domain_guidance_txt}
- Story: {story_text}
- Genre: {genre}
- Mood: {mood_str}
- Dialect: {dialect}

## PRIORITY ORDER (when rules conflict)
1. Every line sounds natural and is something a real person would say.
2. The story is coherent and in order.
3. Clean rhyme and rhythm.
4. Target words.

## RED LINES (a song that crosses any of these FAILS, no matter how well it does elsewhere)
1. Awkward or stiff lines. Any line that sounds unnatural, distorted, inverted, overly poetic, or padded to fit a rhyme. If a native speaker would not say it, the song fails.
2. Breaking the story. Any line that does not belong to the one story, contradicts it, or sits outside the setting.
3. Abrupt jumps. Any sudden shift in time, place, speaker, or topic that the learner cannot follow.
4. Losing the educational value. The song must stay useful learning content: every line a real, reusable sentence. No empty emotional filler, vague imagery, or lines that teach nothing a learner could say in real life.
5. Unclear speakers. Any "he", "they", or fact that the speaker could not realistically know in the scene.

If a target word can only be used by crossing a red line, drop it. Red lines always beat word coverage.

## TARGET WORDS
{target_words_philosophy}{domain_target_rule}- Before dropping any word, first try to use it in a different context or story detail. Try at least two other natural contexts (a different speaker, a different line, a different angle on the scene).
- Drop a word only if every attempt sounds forced, awkward, or breaks the story.
- Never force a word in just for coverage.
- If a character's role matches a target word (for example, a "director" character and the word "director"), use it.
- Inflected forms are fine (plural, tense, "every day").
- Sensitive words (kill, terrorist, etc.) only in ordinary or figurative everyday use, otherwise skip.
- Use one consistent variety of English in the whole song. Never mix American and British forms.

## STORY RULES
- Plan the story silently first: setting, characters, 5-6 events in time order, ending, and where each target word fits naturally.
- Every character who speaks or is mentioned must be named or clearly identified. No unexplained "he" or "they."
- One place, one continuous situation. Memories are allowed only if they directly support the conflict.
- Every line advances or deepens the story. No random imagery, no jumps outside it.

## LINE QUALITY RULES
- Each line is 6-9 syllables. Verses all have the same number of lines.
- Test every line: would a native speaker say this to the person in this scene? If not, rewrite it.
- No: poetic or abstract metaphors, inverted word order, filler to fit rhyme ("this way", "I'd say", "all along" as padding), stacked clichés.
- If a perfect rhyme forces an awkward line, use a near rhyme or rewrite both lines.
- Prefer direct sentences a learner can reuse in real life.

## CHORUS & SUNO RULES
{chorus_rule}- Write numbers as words. No parentheses, ad-libs, or sound effects inside lyrics.
- Avoid hard-to-pronounce words at the end of lines.

## SELF-CHECK (do silently, then fix before output)
For every line: natural? in story order? right length? dialect consistent? no filler? Is each target word used in its natural everyday meaning, not forced? For every word left out: did I try at least two other natural contexts before dropping it?
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
