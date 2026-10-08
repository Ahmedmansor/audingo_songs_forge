import sys, os, re
sys.path.insert(0, os.path.abspath("."))

# Mock streamlit session state and report
theme_val = "Street & Daily Life"
genre_val = "Cinematic / Ballad"
concept_val = "Two former best mates meet in a quiet diner to clear up rumors."
concept_val = re.sub(r"\bmates\b", "friends", concept_val, flags=re.I)
concept_val = re.sub(r"\bmate\b", "friend", concept_val, flags=re.I)

target_words_list = ["mom", "mistake", "listen", "quiet"]
words_joined = ", ".join(target_words_list)

lyrics_text = """[Verse 1]
Sitting in this diner with my old friend
Trying to figure out where we went wrong
[Chorus]
It's killing me to lose my best friend
I'm not mad at you anymore"""

lines_breakdown = [
    {"line": "Sitting in this diner with my old friend", "score": 94, "status": "✅", "comment": "Natural and grounded."},
    {"line": "Trying to figure out where we went wrong", "score": 92, "status": "✅", "comment": "Good cadence."},
    {"line": "It's killing me to lose my best friend", "score": 85, "status": "✅", "comment": "Slightly melodramatic for ESL."}, # Score 85 should NOT be locked!
    {"line": "I'm not mad at you anymore", "score": 78, "status": "⚠️", "comment": "Needs better rhythm."}
]

# Strict Green lock rule: score must be >= 90 AND status must be ✅
passed_lines = [l for l in lines_breakdown if l.get("status") == "✅" and l.get("score", 0) >= 90]
critical_lines = [l for l in lines_breakdown if l.get("status") in ["❌", "🗑️"] or l.get("score", 0) < 70]
warning_lines = [l for l in lines_breakdown if (l.get("status") == "⚠️") or (l.get("status") == "✅" and l.get("score", 0) < 90)]

crit_text = "\n".join([f'- Line: "{l.get("line", "")}"\n  Score: {l.get("score", 0)}%\n  Critique: {l.get("comment", "")}' for l in critical_lines]) if critical_lines else "None (All lines passed critical checks!)"
warn_text = "\n".join([f'- Line: "{l.get("line", "")}"\n  Score: {l.get("score", 0)}%\n  Critique: {l.get("comment", "")}' for l in warning_lines]) if warning_lines else "None"
passed_text = "\n".join([f'- "{l.get("line", "")}"' for l in passed_lines]) if passed_lines else "None"

status_dict = {}
for l in lines_breakdown:
    raw_txt = l.get("line", "").strip().lower()
    score = l.get("score", 0)
    st_val = l.get("status", "✅")
    if st_val in ["❌", "🗑️"] or score < 70:
        eff_status = "❌"
    elif st_val == "⚠️" or score < 90:
        eff_status = "⚠️"
    else:
        eff_status = "✅"
    if raw_txt:
        status_dict[raw_txt] = eff_status

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

external_prompt = f"""You are an expert English linguist and a professional ESL teacher who edits song lyrics for learners.
Your mission is to perform SURGICAL REPAIRS on the song lyrics below.

THE GOAL: the learner should be able to memorize ANY single line and use it as-is in real life. Every line must be a natural sentence a native speaker would actually say, and it must make sense when read alone.

CRITICAL PEDAGOGICAL MISSION:
This song is an educational song built around a strict list of target vocabulary words.
Every target word that is currently in the lyrics MUST be preserved. Do not add target words that are missing. Dropping or replacing a present target word with a synonym is a critical failure.

CONTEXTUAL ANCHORS:
- Theme: "{theme_val}"
- Musical Genre: "{genre_val}"
- Core Story / Setting / Concept: "{concept_val}"
- Dialect: American English (never mix dialects; replace British-only words like "mate" unless they are protected target words in a locked line)

🎯 TARGET VOCABULARY (Preserve every target word currently in the lyrics; do not add missing ones):
{words_joined}

🔒 VERIFIED GREEN LINES ({len(passed_lines)} Lines - 100% LOCKED, DO NOT CHANGE):
{passed_text}

🚨 CRITICAL FLAWED LINES (Must be rewritten - Status ❌):
{crit_text}

⚠️ MINOR WARNING LINES (Only tweak if it improves flow - Status ⚠️):
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

D. IMPROVEMENT GOALS FOR EDITED LINES (priority order):
   1. THEMATIC CONSISTENCY & SETTING CONTINUITY: Every edited line must stay inside the song's theme ("{theme_val}") and established setting / story ("{concept_val}"). Do not introduce new locations, characters, or topics that drift away from the central story. If a line does not serve the core story, rewrite it.
   2. PRACTICAL USABILITY:
      - An ESL learner who memorizes the line should be able to say it naturally in real life. Prefer everyday spoken English over poetic or literary phrasing.
      - Use natural contractions (I'm, don't, can't); avoid stiff forms.
      - Standalone test: read alone, the line must be natural and useful.
   3. NO FORCED RHYME: A line must add real narrative meaning, not exist only to rhyme.
   4. NO REPETITION: Avoid repeating the same opening word or key noun in nearby lines.
   5. FLOW & MELODY: Keep syllable count (±1) and rhyme scheme so the melody still fits.
   6. LENGTH: 6 to 9 syllables per edited line (±1).

E. FINAL SELF-CHECK (execute silently before outputting):
   - Count green lines: none missing, none changed, none repositioned.
   - Verify all present target words are still preserved.
   - Ensure each edited line passes goals 1 to 6 (including Standalone test and 6-9 syllables).
   - If a yellow line cannot be improved, keep it as is.

F. OUTPUT FORMAT:
   Part 1: The complete clean lyrics (without any [🔒], [🚨], or [⚠️] tags), ready to paste.
   Part 2: Change log, one line per edited line:
   "Original line" → "New line" | Reason for change
   (If nothing was edited, write "No edits needed".)
   
   === REVIEW ===
   Part 3: GREEN LINE REVIEW (suggestions only, NOT applied to Part 1).
   Check the green lines against goals D1 to D6, plus:
   - Flag any green line that breaks thematic consistency or setting continuity.
   - Is the line natural spoken English a learner can reuse in daily life?
   - Is the register (rude, formal, poetic, profane) flagged for the learner?
   - Is there weak coherence, forced rhyme, or repetition across the whole song?
   - Does any green line clash with an edit made in Part 1?
   Only mention a green line if you have a REAL, specific improvement. Do not pad the list. For each one give:
   "Original → Suggested | reason | priority (high / medium / low)"
   If nothing is worth changing, write "Green lines are solid, no suggestions."
   Finish with a verdict: overall coherence, educational value, and whether the song is ready to publish.

G. NEVER apply Part 3 suggestions to Part 1 unless the user explicitly approves them in the next message."""

print("Length of prompt:", len(external_prompt))
print("\n--- TEST CHECKS ---")
print("1. Has Story:", 'Core Story / Setting / Concept: "Two former best friends' in external_prompt)
print("2. Has Dialect:", '- Dialect: American English' in external_prompt)
print("3. Has THE GOAL:", 'THE GOAL:' in external_prompt)
print("4. Has Standalone test:", 'Standalone test: read alone' in external_prompt)
print("5. Has 6-9 syllables:", '6 to 9 syllables per edited line' in external_prompt)
print("6. Score 85 is Yellow, not Locked:", "[⚠️ OPTIONAL POLISH] It's killing me" in external_prompt)
print("7. Target words preserve phrase:", "Every target word that is currently in the lyrics MUST be preserved" in external_prompt)
