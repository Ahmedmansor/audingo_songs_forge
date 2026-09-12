"""
prompt_builder.py — Constructs the Master Prompt for external LLMs (Claude, GPT-4o)
to generate song lyrics, title, and Suno AI music style prompts.
"""

from typing import List, Dict, Any


def generate_master_prompt(
    target_words: List[str],
    genre: str,
    song_structure: str,
    mood_analysis: Dict[str, Any],
    creative_concept: str = ""
) -> str:
    """
    Format a complete, production-ready Master Prompt ready to be copied into Claude / GPT-4o.
    """
    words_list_formatted = "\n".join(f"- **{w}**" for w in target_words)
    
    # Sort moods by percentage desc
    mood_items = sorted(
        mood_analysis.items(),
        key=lambda item: item[1] if isinstance(item[1], (int, float)) else 0,
        reverse=True
    )
    mood_str = ", ".join(f"{k}: {v}%" for k, v in mood_items if v > 0)

    prompt = f"""# 🎵 MASTER SONGWRITING & SUNO PROMPT

You are a world-class songwriter, hitmaker producer, and English language pedagogy expert.
Your mission is to write a radio-ready, memorable hit song that naturally weaves 20 specific target vocabulary words into vivid, emotionally compelling lyrics.

---

### 🎯 Mandatory Target Vocabulary (All 20 words MUST appear):
{words_list_formatted}

*(Note: Inflected forms like plurals, verb tenses, etc. are allowed, but keeping them close to base form is preferred).*

---

### 🎨 Creative Direction:
- **Genre & Style:** {genre}
- **Song Structure:** {song_structure}
- **Emotional Mood Profile:** {mood_str if mood_str else "Catchy, uplifting, energetic"}
- **Core Concept / Story:** {creative_concept if creative_concept else "An engaging story that flows naturally without sounding like an educational list."}

---

### 📝 Generation Instructions:
1. **Title:** Propose a catchy, punchy song title.
2. **Suno Style Prompt (under 120 chars):** Provide a dense, keyword-rich Suno v3.5/v4 prompt (e.g. `Synth-pop, 128 bpm, female vocals, shimmering synthesizers, driving 80s bassline, anthemic chorus`).
3. **Full Lyrics:**
   - Follow the structure: `{song_structure}`.
   - Label each section clearly: `[Verse 1]`, `[Pre-Chorus]`, `[Chorus]`, `[Verse 2]`, `[Bridge]`, `[Outro]`, etc.
   - **Bold** every target word when it appears in the lyrics so it is easy to verify (e.g. **{target_words[0] if target_words else "word"}**).
   - Ensure the lyrics flow musically, with natural meter, singable phrasing, and authentic emotional rhyme schemes.
   - AVOID forced rhymes or robotic phrasing. It must feel like a real commercial song!
"""
    return prompt
