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

    return f"""You are an elite music producer, ESL pedagogy specialist, and master lyricist analyzing a specific vocabulary batch for educational songwriting.

CONTEXT: These words will be crafted into a radio-ready song designed for English language learners. The song must weave these words into authentic, practical real-life human experiences and conversational dialogue — NOT in abstract metaphors or fantasy tropes.

Here is the batch of 20 target vocabulary words:
{words_str}

Available Genres (ALL 13 genres below are pre-curated for ESL vocal clarity with upfront, crystal-clear vocals):
{genres_str}

Available Song Structures:
{structures_str}

Available Mood Categories (Percentages MUST sum up to exactly 100):
{moods_str}

CRITICAL DIRECTIVE 1: FULL HUMAN EMOTIONAL SPECTRUM (DO NOT DEFAULT TO HAPPY / UPLIFTING):
- Real human life encompasses a rich tapestry of emotions:
  * Sadness, heartbreak, painful goodbyes, disappointment, separation, loneliness, or grieving a loss -> MUST select "Sad / Heartbroken" or "Nostalgic / Melancholic".
  * Deep nostalgia, reminiscing on old memories, homesickness, childhood, longing -> "Nostalgic / Melancholic".
  * High-stakes personal crossroads, intense drama, heated arguments, confrontation, pressure -> "Dramatic / Intense" or "Dark / Moody".
  * Romantic chemistry, tender confessions, vulnerability, butterflies -> "Romantic / Sweet".
  * Pure funk, weekend party, high adrenaline, celebration, triumph -> "Energetic" or "Playful / Quirky".
  * Laid-back contentment, lazy rainy Sunday, unwinding after a long week -> "Chill / Relaxed".
  * Genuine optimism, breakthroughs, shared triumphs -> "Happy" or "Uplifting / Inspiring".
- If the words convey struggle, hardship, difficulty, loss, or heavy emotional weight, DO NOT force an artificial happy ending or default to "Uplifting". Dive deep into authentic poignant sentiment!
- Be decisive in your percentages: let the dominant emotional tone lead strongly (e.g., 60-80%).

CRITICAL DIRECTIVE 2: DIVERSE GENRE MATCHING (BREAK THE ACOUSTIC / INDIE-POP MONOPOLY):
- DO NOT default repeatedly to "Acoustic / Folk" or "Indie Pop". Actively choose from the diverse genre palette based on emotional fit:
  * Emotional heartbreak, sorrow, or grand vocal moments -> "Cinematic / Ballad", "R&B / Contemporary Soul", "Lo-Fi / Chillhop", "Country / Americana"
  * Romantic, tender, or soulful moments -> "R&B / Contemporary Soul", "Jazz / Bossa Nova", "Pop"
  * High energy, celebration, dance, groove -> "Funk / Disco Groove", "Synth-Pop / 80s Retro", "K-Pop Style (Clear English Vocals)", "Pop"
  * Nostalgic retro vibes, night drives, tension -> "Synth-Pop / 80s Retro", "Cinematic / Ballad", "Lo-Fi / Chillhop"
  * Relaxed, mellow, introspective, everyday coffee shop -> "Lo-Fi / Chillhop", "Melodic Chill Electronic", "Jazz / Bossa Nova", "Reggae / Tropical Pop"
  * Rootsy storytelling, everyday blue-collar struggles, journey -> "Country / Americana", "Acoustic / Folk"

CRITICAL STORY CONCEPT INSTRUCTIONS:
- Ground the story in a vivid, relatable slice-of-life scenario with real spoken dialogue and human stakes.
- Explore diverse domains:
  * Emotional turning points: Packing bags for a move, an emotional late-night phone call, a difficult confession, parting ways at an airport, returning to a childhood hometown.
  * Relationships: First date jitters, apologizing after a misunderstanding, quiet reassurance during tough times, celebrating an anniversary.
  * Daily life & struggles: Overcoming burnout, a tough shift, budgeting for rent, fixing up a beat-up car, preparing for a life-changing interview.
  * Friendship & fun: Impromptu diner conversations, laughing through mistakes, road-tripping with the radio on, a bustling weekend market.
- NO corporate cubicle monotony, NO abstract surreal metaphors. Keep it conversational, cinematic, and genuinely human.

Return a valid JSON object with the following exact schema:
{{
    "mood_breakdown": {{
        "Category Name": integer_percentage, ...
    }},
    "genre": "Exact match from Available Genres",
    "song_structure": "Exact match from Available Song Structures",
    "creative_concept": "1-2 sentences describing an engaging, authentic real-life scenario or human storyline that weaves these words naturally into spoken dialogue and realistic actions."
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
                    temperature=0.85,
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


def build_poster_prompt_instruction(title: str, lyrics: str, genre: str, vocalist: str) -> str:
    """Build the prompt engineering instruction for generating an image generation prompt."""
    sample_lyrics = lyrics[:1500] if lyrics else "No lyrics provided."

    return f"""You are an elite AI art director and prompt engineer specializing in hyper-detailed album cover prompts for Midjourney, DALL-E 3, and modern AI image generators.

Generate a single, comprehensive, visually striking image generation prompt for a commercial music album cover poster.

[SONG DETAILS]
- Title: {title}
- Musical Genre: {genre}
- Lead Vocalist/Artist Persona: {vocalist}
- Lyrics Atmosphere & Context:
\"\"\"
{sample_lyrics}
\"\"\"

[STRICT DESIGN GUIDELINES]
1. Visual Text: The exact song title "{title}" must be incorporated as stylized, integrated typographic text on the cover art (e.g. bold vintage typography, neon sign, embossed metallic lettering, or artistic overlay fitting the {genre} style).
2. Genre Aesthetics: The visual aesthetic, lighting, color grading, camera lens, and texture must perfectly embody the {genre} music genre.
3. Artist/Subject: Feature a compelling character or silhouette fitting the {vocalist} description, seamlessly blended into the environment with expressive mood, wardrobe, and atmosphere derived from the lyrics.
4. Scene & Mood: Capture the emotional narrative and energy of the song. Evoke cinematic atmosphere, depth of field, vivid atmospheric lighting effects (e.g. volumetric lighting, mist, lens flare, cinematic film grain, or clean modern render appropriate to {genre}).
5. Output Format:
   - Provide ONLY the raw text prompt.
   - Do NOT include any intro ("Here is the prompt:"), markdown code blocks, quotes, or explanations.
   - End the prompt with aspect ratio parameter: --ar 1:1
"""


def generate_poster_prompt(title: str, lyrics: str, genre: str, vocalist: str) -> Dict[str, Any]:
    """
    Generate an AI image generator prompt (Midjourney/DALL-E style) for a song poster/album cover.
    Cycles through PREFERRED_MODELS in case of error.
    """
    from google.genai import types

    client = get_gemini_client()
    instruction = build_poster_prompt_instruction(title, lyrics, genre, vocalist)

    last_error = None

    for model_name in PREFERRED_MODELS:
        try:
            logger.info("Generating poster prompt with model: %s", model_name)
            response = client.models.generate_content(
                model=model_name,
                contents=instruction,
                config=types.GenerateContentConfig(
                    temperature=0.8,
                ),
            )
            raw = response.text.strip()
            
            # Clean possible markdown wrap
            if raw.startswith("```"):
                lines = raw.splitlines()
                raw = "\n".join(
                    line for line in lines if not line.strip().startswith("```")
                ).strip()

            # Ensure --ar 1:1 suffix
            if not raw.endswith("--ar 1:1"):
                raw = f"{raw} --ar 1:1"

            return {
                "success": True,
                "model_used": model_name,
                "prompt": raw
            }
        except Exception as exc:
            logger.warning("Poster prompt generation failed with %s: %s", model_name, exc)
            last_error = exc
            continue

    return {
        "success": False,
        "error": str(last_error),
        "prompt": ""
    }


def generate_studio_poster_prompt(
    concept: str,
    genre: str,
    vocalist: str,
    title: str = "[Song Title]"
) -> str:
    """
    Generate a high-end Midjourney/DALL-E album cover prompt in Studio mode
    based on the story concept, genre, and vocalist persona.
    Cycles through preferred models, returning high-quality fallback on failure.
    """
    from google.genai import types

    client = get_gemini_client()
    clean_concept = concept.strip() if concept else "A vibrant, relatable real-life narrative."
    instruction = f"""You are an elite AI art director and prompt engineer specializing in hyper-detailed album cover prompts for Midjourney, DALL-E 3, and modern AI image generators.

Generate a single, comprehensive, visually striking image generation prompt for a commercial music album cover poster.

[SONG DETAILS]
- Musical Genre: {genre}
- Lead Vocalist/Artist Persona: {vocalist}
- Story Concept & Theme:
\"\"\"
{clean_concept}
\"\"\"
- Song Title for Typography: "{title}"

[STRICT DESIGN GUIDELINES]
1. Visual Text & Typography: Include instructions to incorporate the song title "{title}" as stylized, artistic integrated lettering fitting the {genre} genre (e.g. glowing neon, minimalist clean sans-serif, vintage embossed, or handwritten aesthetic).
2. Genre Aesthetics: The visual aesthetic, lighting, color grading, camera lens (e.g. 35mm film, anamorphic, Hasselblad medium format), and atmosphere must perfectly embody {genre}.
3. Artist/Subject: Feature a character, silhouette, or aesthetic fitting {vocalist}, naturally set in a cinematic real-life scene matching the story concept.
4. Scene & Mood: Capture the emotional narrative and lighting (golden hour, neon night, volumetric mist, soft morning window light).
5. Output Format:
   - Provide ONLY the raw text prompt.
   - Do NOT include any markdown code blocks, quotes, or conversational intros.
   - End the prompt with aspect ratio parameter: --ar 1:1
"""
    for model_name in PREFERRED_MODELS:
        try:
            logger.info("Generating studio poster prompt with model: %s", model_name)
            response = client.models.generate_content(
                model=model_name,
                contents=instruction,
                config=types.GenerateContentConfig(
                    temperature=0.8,
                ),
            )
            raw = response.text.strip()
            if raw.startswith("```"):
                lines = raw.splitlines()
                raw = "\n".join(
                    line for line in lines if not line.strip().startswith("```")
                ).strip()
            if not raw.endswith("--ar 1:1"):
                raw = f"{raw} --ar 1:1"
            return raw
        except Exception as exc:
            logger.warning("Studio poster prompt generation failed with %s: %s", model_name, exc)
            continue

    # High-quality offline fallback
    fallback_char = f"silhouette of a {vocalist.lower()} artist" if vocalist != "Instrumental" else "atmospheric architectural landscape"
    short_concept = clean_concept[:120].strip()
    return (
        f"Cinematic album cover for a {genre} track, featuring {fallback_char} in an evocative scene inspired by {short_concept}. "
        f"Atmospheric volumetric lighting, rich color grading, shallow depth of field, 35mm photograph texture, "
        f"tastefully integrated artistic typography reading '{title}', highly detailed, award-winning cover art --ar 1:1"
    )


def build_variant_instruction(title: str, lyrics: str, genre: str, vocalist: str) -> str:
    """Build the unified JSON prompt engineering instruction for Suno music prompt and Midjourney/DALL-E poster prompt."""
    sample_lyrics = lyrics[:1500] if lyrics else "No lyrics provided."

    return f"""You are an expert AI creative director for a music production SaaS. Your task is to generate both a music generation prompt (for Suno AI) and an album cover prompt (for Midjourney/DALL-E) based on the song details.

[INPUT DATA]
- Song Title: {title}
- Song Theme/Lyrics summary:
\"\"\"
{sample_lyrics}
\"\"\"
- Target Genre: {genre}
- Vocalist Gender: {vocalist}

[RULES FOR SUNO MUSIC PROMPT]
1. Must be strictly UNDER 120 characters.
2. Format as a comma-separated list of keywords.
3. Must explicitly include the {genre}, the {vocalist} lead vocals, and descriptors for clear, upfront vocals to ensure lyrical clarity.
4. Include a steady BPM appropriate for the genre (e.g., 112 bpm).
5. Examples:
   - "Synthwave, steady 112 bpm, clear upfront male vocals, warm analog synths, pulsing bass, retro drum machine, clean mix"
   - "Melodic chill electronic, soft piano, warm ambient synth pads, steady 112 bpm, clear upfront vocals, deep relaxed bass, clean atmospheric mix"

[RULES FOR POSTER IMAGE PROMPT]
1. Create a detailed, aesthetic visual prompt that perfectly matches the {genre} vibe and the lyrics theme.
2. Feature a {vocalist} character or silhouette (or ambient aesthetic if instrumental).
3. Include lighting, color grading, and camera aesthetic details.
4. TYPOGRAPHY INTEGRATION: You MUST include instructions to artistically render the exact song title "{title}" into the image. Describe how the typography should look so it blends perfectly with the genre's aesthetic (e.g., "bold integrated gold-leaf serif lettering", "glowing neon futuristic font saying '{title}'").
5. End with --ar 1:1.

[OUTPUT FORMAT]
You MUST output ONLY a valid JSON object with this exact schema:
{{
  "suno_prompt": "string",
  "poster_prompt": "string"
}}
"""


def generate_track_variant(title: str, lyrics: str, genre: str, vocalist: str) -> Dict[str, Any]:
    """
    Generate both Suno music prompt and Midjourney/DALL-E poster prompt for a song style variant.
    Uses JSON response mode and cycles through PREFERRED_MODELS in case of rate limits or errors.
    """
    from google.genai import types

    client = get_gemini_client()
    instruction = build_variant_instruction(title, lyrics, genre, vocalist)

    last_error = None

    for model_name in PREFERRED_MODELS:
        try:
            logger.info("Generating track variant with model: %s", model_name)
            response = client.models.generate_content(
                model=model_name,
                contents=instruction,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7,
                ),
            )
            raw = response.text.strip()
            
            # Clean possible markdown wrap
            if raw.startswith("```"):
                lines = raw.splitlines()
                raw = "\n".join(
                    line for line in lines if not line.strip().startswith("```")
                ).strip()

            data = json.loads(raw)
            suno_prompt = str(data.get("suno_prompt", "")).strip()
            poster_prompt = str(data.get("poster_prompt", "")).strip()

            # Ensure --ar 1:1 suffix on poster prompt
            if poster_prompt and not poster_prompt.endswith("--ar 1:1"):
                poster_prompt = f"{poster_prompt} --ar 1:1"

            return {
                "success": True,
                "model_used": model_name,
                "suno_prompt": suno_prompt,
                "poster_prompt": poster_prompt
            }
        except Exception as exc:
            logger.warning("Track variant generation failed with %s: %s", model_name, exc)
            last_error = exc
            continue

    # Fallback if all models fail
    return {
        "success": False,
        "error": str(last_error),
        "suno_prompt": f"{genre}, steady tempo, clear upfront {vocalist.lower()} vocals, clean mix",
        "poster_prompt": f"Cinematic album cover for '{title}', {genre} aesthetic, featuring {vocalist.lower()} artist, typography displaying '{title}', dramatic lighting, album art --ar 1:1"
    }
