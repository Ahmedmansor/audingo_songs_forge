"""
gemini_client.py — Gemini API integration with model fallback and mood/genre analysis.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from constants import GENRES, SONG_STRUCTURES, MOOD_CATEGORIES, GEMINI_MODEL_CANDIDATES

load_dotenv()
logger = logging.getLogger(__name__)

# Preferred model order as specified by user:
# 1. Gemini 3 Flash (models/gemini-3-flash-preview)
# 2. Gemini 3.5 Flash Lite (models/gemini-3.5-flash-lite)
# 3. Gemini 3.1 Flash Lite (models/gemini-3.1-flash-lite-preview)
PREFERRED_MODELS = GEMINI_MODEL_CANDIDATES



def get_gemini_client():
    """Initialize and return google-genai Client."""
    from google import genai
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment or .env file.")
    return genai.Client(api_key=api_key)


def build_analysis_prompt(words: List[str]) -> str:
    """Build the JSON schema instruction prompt for Gemini."""
    words_str = ", ".join(words)
    genres_str = "\n".join(f"- {g}" for g in GENRES)
    structures_str = "\n".join(f"- {s}" for s in SONG_STRUCTURES)
    moods_str = "\n".join(f"- {m}" for m in MOOD_CATEGORIES)

    return f"""You are an expert music producer, ESL pedagogy specialist, and creative lyricist analyzing a specific vocabulary set for educational songwriting.

CONTEXT: These words will be turned into a song designed for English language learners. The song must use these words in practical, conversational, real-life human contexts — NOT in poetic metaphors or abstract themes.

Here is the batch of 20 target vocabulary words:
{words_str}

Analyze how these words connect to authentic real-life situations, interpersonal relationships, emotional turning points, or engaging everyday storylines.
You MUST choose the genre and structure ONLY from the provided closed lists below. Do NOT invent new genres or structures.
Choose a genre where vocals are always upfront and crystal clear — this is for language learning, so clarity is paramount.

Available Genres (all optimized for vocal clarity):
{genres_str}

Available Song Structures:
{structures_str}

Available Mood Categories (Percentages MUST sum up to exactly 100):
{moods_str}

CRITICAL PERCENTAGE DISTRIBUTION INSTRUCTION:
Do NOT evenly distribute the percentages. Be highly decisive. If the 20 words strongly lean towards a specific mood, allow that primary mood to dominate the score (e.g., 70%, 80%, or even 90%). Avoid safe, flat distributions. Only mix percentages closely if the vocabulary is genuinely conflicting. The total must still exactly equal 100.

CREATIVE STORY CONCEPT INSTRUCTIONS (CRITICAL FOR VARIETY & RELATABILITY):
- DO NOT default to office work, corporate cubicles, booting up computers, desk jobs, or paperwork. That is repetitive, boring, and uncreative.
- Everyday practical life is rich, varied, and social. Explore diverse, vibrant, relatable human contexts across life domains:
  * Social & Friendships: Catching up with friends at a bustling café, weekend road trip, funny diner conversations, laughing through misadventures.
  * Home & Everyday Living: Cooking a meal together, moving to a new neighborhood, DIY repairs, weekend market shopping, personal morning rituals.
  * Relationships & Dating: The excitement/nerves of a first date, overcoming a misunderstanding, late-night phone calls, planning a surprise.
  * Hobbies, Sports & Health: Training for a personal goal, gym/outdoor fitness, learning a creative craft, playing an instrument, health and wellness.
  * Urban Life & Travel: Exploring an unfamiliar street, catching a train/flight, navigating public transit, spontaneous neighborhood discoveries.
  * Everyday Dilemmas & Life Choices: Budgeting for a dream purchase, making a tough personal choice, overcoming daily obstacles with optimism.
  * If tech/work words are present, frame them in modern human ways (e.g., a freelancer at a coffee shop, helping a friend with a project, working on a creative hobby) — NEVER a generic corporate desk routine.
- The concept MUST feel like a relatable, cinematic snapshot of real life that an ordinary person lives and speaks about in daily conversation.
- NO abstract metaphors, NO fantasy, NO corporate monotony.

Return a valid JSON object with the following exact schema:
{{
    "mood_breakdown": {{
        "Category Name": integer_percentage, ...
    }},
    "genre": "Exact match from Available Genres",
    "song_structure": "Exact match from Available Song Structures",
    "creative_concept": "1-2 sentences describing an engaging, authentic real-life scenario or human storyline (from the diverse everyday domains above — NEVER an office desk routine) that weaves these words naturally into spoken dialogue and realistic actions."
}}
"""


def analyze_vocabulary_mood(words: List[str]) -> Dict[str, Any]:
    """
    Send the 20 words to Gemini to get mood breakdown, genre, and structure recommendations.
    Cycles through preferred models if rate limits or errors occur.
    """
    from google.genai import types

    client = get_gemini_client()
    prompt = build_analysis_prompt(words)
    
    last_error = None
    
    for model_name in PREFERRED_MODELS:
        try:
            logger.info("Calling Gemini with model: %s", model_name)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                ),
            )
            raw = response.text.strip()
            
            # Clean possible markdown blocks
            if raw.startswith("```"):
                lines = raw.splitlines()
                raw = "\n".join(
                    line for line in lines if not line.strip().startswith("```")
                ).strip()
                
            data = json.loads(raw)
            
            # Basic validation
            genre = data.get("genre", GENRES[0])
            if genre not in GENRES:
                genre = GENRES[0]
                
            structure = data.get("song_structure", SONG_STRUCTURES[0])
            if structure not in SONG_STRUCTURES:
                structure = SONG_STRUCTURES[0]
                
            mood_breakdown = data.get("mood_breakdown", {})
            
            return {
                "success": True,
                "model_used": model_name,
                "mood_breakdown": mood_breakdown,
                "genre": genre,
                "song_structure": structure,
                "creative_concept": data.get("creative_concept", "")
            }
        except Exception as exc:
            logger.warning("Failed with model %s: %s. Trying next fallback model...", model_name, exc)
            last_error = exc
            continue

    # If all models fail, return safe default
    return {
        "success": False,
        "error": str(last_error),
        "model_used": "Fallback Defaults",
        "mood_breakdown": {
            "Happy": 30,
            "Energetic": 30,
            "Uplifting / Inspiring": 20,
            "Chill / Relaxed": 20
        },
        "genre": GENRES[0],
        "song_structure": SONG_STRUCTURES[0],
        "creative_concept": "A vibrant and catchy song weaving the target vocabulary together."
    }
