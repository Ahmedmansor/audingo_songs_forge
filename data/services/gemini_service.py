"""
gemini_service.py — Gemini API integration with model fallback and mood/genre analysis.
"""

import json
import logging
import os
import sqlite3
from domain.services.story_policy import build_story_direction
from data.repositories.song_repository import get_recent_story_concepts
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

from constants import (
    GENRES,
    SONG_STRUCTURES,
    MOOD_CATEGORIES,
    GEMINI_MODEL_CANDIDATES,
    get_category_profile,
    sample_domain_creative_sparks,
)

load_dotenv()
logger = logging.getLogger(__name__)

PREFERRED_MODELS = GEMINI_MODEL_CANDIDATES


def get_gemini_api_keys() -> List[str]:
    """Retrieve all available Gemini API keys from environment or .env in order."""
    from dotenv import load_dotenv
    load_dotenv(override=True)

    keys = []
    k1 = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if k1:
        keys.append(k1)
    k2 = (os.environ.get("GEMINI_API_KEY_2") or "").strip()
    if k2 and k2 not in keys:
        keys.append(k2)
    for i in range(3, 10):
        extra_k = (os.environ.get(f"GEMINI_API_KEY_{i}") or "").strip()
        if extra_k and extra_k not in keys:
            keys.append(extra_k)

    return keys


def get_gemini_client(api_key: Optional[str] = None):
    """Initialize and return google-genai Client with specified or primary key."""
    from google import genai
    if api_key:
        return genai.Client(api_key=api_key)

    keys = get_gemini_api_keys()
    if not keys:
        raise ValueError("GEMINI_API_KEY is not set in environment or .env file.")
    return genai.Client(api_key=keys[0])


def _story_direction(domain):
    try:
        recent = get_recent_story_concepts(domain)
    except sqlite3.Error:
        # Legacy databases may not yet have story tags; never migrate on a prompt read.
        logger.warning("Recent story context unavailable; generating without history.")
        recent = []
    return build_story_direction(domain, get_category_profile(domain), recent)


def build_analysis_prompt(
    words: List[str],
    domain: str = "Basic / Neutral",
    sparks: Optional[Dict[str, Any]] = None,
    existing_concept: Optional[str] = None,
) -> str:
    """Build the JSON schema instruction prompt for Gemini, anchored in the selected vocabulary domain."""
    words_str = ", ".join(words)
    genres_str = "\n".join(f"- {g}" for g in GENRES)
    structures_str = "\n".join(f"- {s}" for s in SONG_STRUCTURES)
    moods_str = "\n".join(f"- {m}" for m in MOOD_CATEGORIES)

    profile = get_category_profile(domain)
    if sparks is None:
        sparks = sample_domain_creative_sparks(domain)

    settings_bullets = (
        "\n".join(f"  * {s}" for s in sparks.get("sampled_settings", []))
        if sparks.get("sampled_settings")
        else f"  * {profile.get('setting', 'Authentic real-world situations')}"
    )
    conflicts_bullets = (
        "\n".join(f"  * {c}" for c in sparks.get("sampled_conflicts", []))
        if sparks.get("sampled_conflicts")
        else "  * A realistic human challenge or decision"
    )
    directive = profile.get("domain_directive", "")

    if existing_concept and existing_concept.strip():
        concept_block = f"""EXISTING APPROVED STORY SCENARIO:
"{existing_concept.strip()}"

CRITICAL MANDATE:
- The user/pipeline has ALREADY established this specific story scenario for the 20 target words.
- DO NOT replace or invent a contradictory or completely different scenario!
- Analyze the 20 target words IN THE DIRECT CONTEXT OF THIS STORY SCENARIO to determine:
  1. The authentic emotional mood breakdown (percentages summing to exactly 100) that best fits this story and vocabulary.
  2. The ideal musical genre and song structure that will deliver upfront, crystal-clear ESL vocals for this specific scenario.
- In "creative_concept", preserve and reflect this exact scenario (you may subtly refine phrasing or keep it verbatim, but preserve the exact characters, setting, and plot)."""
    else:
        concept_block = f"""CRITICAL STORY CONCEPT INSTRUCTIONS (SPECIFIC, HIGH-FIDELITY STORYLINE ROADMAP):
In "creative_concept", construct a rich, highly specific 3-4 sentence narrative scenario that explicitly defines:
1. Specific Characters & Relationship:
   - Clearly identified people and a relationship matching '{domain}' and the immediate event.
2. Tangible Physical Setting & Sensory Atmosphere:
   - Establish the immediate human event in a believable place belonging to this domain. Time and physical details are optional and must serve the event.
3. Core Human Stakes & Dramatic Tension:
   - Identify the immediate emotional or practical dilemma that naturally requires the 20 target words to be spoken.
4. Clear Narrative Progression:
   - Let the choices and consequences create progression and an earned ending; follow DYNAMIC STORY DESIGN rather than a preset resolution.
5. Real Spoken Dialogue Anchors:
   - The scene must naturally inspire everyday spoken American English lines that an ESL learner could memorize and use in real life.

- STRICT PROHIBITIONS:
  * NO CLOCK-WATCHING OPENINGS: Never begin the story concept or song lyrics with digital clock readings or alarm announcements (e.g. "It's 5:45 AM", "At 8:30 in the morning"). Start directly in media res with concrete human action, direct spoken words, or sensory atmosphere.
  * NO VOCABULARY CRAMMING (ABSOLUTE ZERO WORD-SALAD): Do NOT attempt to cram, shoehorn, or force the 20 target words into this 3-4 sentence concept text! Doing so creates an absurd, robotic, unreadable "incantation" or vocabulary exam paragraph. The concept summary is merely the theatrical logline / stage setting (characters, situation, emotional stakes). The 20 words will be distributed naturally throughout the full song lyrics later by the lyricist, NOT jammed here. Write the concept in pure, effortless, organic human English.
  * NO verbatim copying: Do NOT copy-paste the suggested props, times, or example sentences word-for-word. They are sparks of inspiration to show the vibe — invent a fresh, original scenario whose physical details emerge naturally from your 20 target words.
  * NO vague one-liners like "Someone faces challenges in life and finds hope".
  * NO corporate textbook clichés or abstract surreal fantasies.
  * Make the scenario so vivid and specific that any songwriter instantly sees the entire scene unfold like a movie scene."""

    return f"""You are an elite music producer, ESL pedagogy specialist, and master lyricist analyzing a specific vocabulary batch for educational songwriting.

AUDINGO EDUCATIONAL MISSION:
The song must weave these 20 target words into an authentic, practical real-life human experience with natural conversational dialogue. English language learners must be able to memorize ANY single line and use it naturally in real life.

Here is the batch of 20 target vocabulary words:
{words_str}

Available Genres (ALL 13 genres below are pre-curated for ESL vocal clarity with upfront, crystal-clear vocals):
{genres_str}

Available Song Structures:
{structures_str}

Available Mood Categories (Percentages MUST sum up to exactly 100):
{moods_str}

CRITICAL PRINCIPLE 1: TARGET WORDS LEAD THE STORY (WORDS FIRST, SCENARIO SECOND):
- Examine the 20 target vocabulary words in front of you first.
- The story scenario MUST naturally provide a real-life situation where characters would speak these words during authentic conversation.
- ABSOLUTELY DO NOT CRAM OR FORCE TARGET WORDS INTO THE CONCEPT SUMMARY: You are defining the movie pitch / stage setting (characters, situation, emotional stakes), NOT writing an ESL test paragraph. Writing a paragraph that packs 10-15 target words together results in an unnatural, robotic "incantation". Keep the concept summary clean, human, and cinematic. The words will be placed naturally into the full lyrics later.
- NEVER bend, distort, or force target words into an unnatural or mismatched setting.
- The thematic domain '{domain}' and the sampled creative sparks below are catalysts to inspire a concrete, vivid scene — choose a storyline where these 20 words fit like a glove.
- THINK OUTSIDE THE BOX & PIVOT FREELY: If the 20 words suggest an unexpected, original real-life scenario within '{domain}' that differs from the suggested sparks, FOLLOW THE WORDS! Never trap yourself in the suggestions. Think outside the box and invent fresh events, settings, and conflicts that give these specific words their most natural, powerful home.

EMOTIONAL AND CONTEXTUAL FIT:
- Choose the actual emotional tone of this situation, including positive, negative or mixed feelings.
- Do not infer tragedy from an isolated word or manufacture optimism to resolve a difficult event.
- Be decisive in your percentages: let the dominant emotional tone lead strongly (e.g., 60-80%).

CRITICAL DIRECTIVE 3: DIVERSE GENRE MATCHING (BREAK THE ACOUSTIC / INDIE-POP MONOPOLY):
- DO NOT default repeatedly to "Acoustic / Folk" or "Indie Pop". Actively choose from the diverse genre palette based on emotional fit:
  * Emotional heartbreak, sorrow, or grand vocal moments -> "Cinematic / Ballad", "R&B / Contemporary Soul", "Lo-Fi / Chillhop", "Country / Americana"
  * Romantic, tender, or soulful moments -> "R&B / Contemporary Soul", "Jazz / Bossa Nova", "Pop"
  * High energy, celebration, dance, groove -> "Funk / Disco Groove", "Synth-Pop / 80s Retro", "K-Pop Style (Clear English Vocals)", "Pop"
  * Nostalgic retro vibes, night drives, tension -> "Synth-Pop / 80s Retro", "Cinematic / Ballad", "Lo-Fi / Chillhop"
  * Relaxed, mellow, introspective, everyday coffee shop -> "Lo-Fi / Chillhop", "Melodic Chill Electronic", "Jazz / Bossa Nova", "Reggae / Tropical Pop"
  * Rootsy storytelling, everyday blue-collar struggles, journey -> "Country / Americana", "Acoustic / Folk"

ACTIVE CATEGORY DOMAIN: "{domain}"

Follow the FINAL STORY AUTHORITY below.

SAMPLE SETTINGS (INSPIRATION SPRINGBOARDS):
{settings_bullets}

SAMPLE CONFLICT ARCHETYPES:
{conflicts_bullets}

DOMAIN-SPECIFIC VOCABULARY & DIALOGUE DIRECTIVE (optional inspiration; DYNAMIC STORY DESIGN takes precedence over legacy plot/ending suggestions):
{directive}

{concept_block}

FINAL STORY AUTHORITY:
{_story_direction(domain)}

Return a valid JSON object with the following exact schema:
{{
    "mood_breakdown": {{
        "Category Name": integer_percentage, ...
    }},
    "genre": "Exact match from Available Genres",
    "song_structure": "Exact match from Available Song Structures",
    "creative_concept": "A specific, vivid 3-4 sentence narrative scenario explicitly defining characters, concrete setting, core tension, and narrative progression, designed to anchor natural spoken dialogue."
}}
"""


def analyze_vocabulary_mood(
    words: List[str],
    domain: str = "Basic / Neutral",
    sparks: Optional[Dict[str, Any]] = None,
    existing_concept: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send the 20 words to Gemini to get mood breakdown, genre, structure, and domain-anchored story concept.
    Uses the strict quality chain: 3.8 Flash, then 3.7 Flash, then 3.6 Flash.
    If existing_concept is provided, Gemini analyzes musical direction anchored directly in that established story.
    """
    from data.services.fallback_engine import generate_with_fallback, CRITIC_FALLBACK_CHAIN

    if sparks is None:
        sparks = sample_domain_creative_sparks(domain)

    prompt = build_analysis_prompt(words, domain=domain, sparks=sparks, existing_concept=existing_concept)

    try:
        raw, model_idx = generate_with_fallback(
            prompt=prompt,
            model_chain=CRITIC_FALLBACK_CHAIN,
            start_index=0,
            require_json=True,
            temperature=0.85,
        )

        data = json.loads(raw)
        model_name = CRITIC_FALLBACK_CHAIN[model_idx]

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
            "creative_concept": data.get("creative_concept", "") or (existing_concept or ""),
            "creative_sparks": sparks,
        }
    except Exception as exc:
        logger.warning("Failed in analyze_vocabulary_mood: %s", exc)
        return {
            "success": False,
            "error": str(exc),
            "model_used": "Fallback Defaults",
            "mood_breakdown": {},
            "genre": GENRES[0],
            "song_structure": SONG_STRUCTURES[0],
            "creative_concept": (
                existing_concept.strip() if (existing_concept and existing_concept.strip()) else
                get_category_profile(domain).get("default_story", f"A deeply human story exploring honest vulnerability and authentic connection in {domain}.")
            ),
            "creative_sparks": sparks,
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
    """Generate an AI image generator prompt (Midjourney/DALL-E style) for a song poster/album cover."""
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
            
            if raw.startswith("```"):
                lines = raw.splitlines()
                raw = "\n".join(
                    line for line in lines if not line.strip().startswith("```")
                ).strip()

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
    """Generate high-end Midjourney/DALL-E album cover prompt in Studio mode."""
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

    fallback_char = f"silhouette of a {vocalist.lower()} artist" if vocalist != "Instrumental" else "atmospheric architectural landscape"
    short_concept = clean_concept[:120].strip()
    return (
        f"Cinematic album cover for a {genre} track, featuring {fallback_char} in an evocative scene inspired by {short_concept}. "
        f"Atmospheric volumetric lighting, rich color grading, shallow depth of field, 35mm photograph texture, "
        f"tastefully integrated artistic typography reading '{title}', highly detailed, award-winning cover art --ar 1:1"
    )


def build_variant_instruction(title: str, lyrics: str, genre: str, vocalist: str) -> str:
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
4. DYNAMIC TEMPO & BPM: Vary the BPM and groove naturally to match this specific song's emotional atmosphere (e.g. relaxed 98 bpm, driving 112 bpm, upbeat 118 bpm, bouncy 124 bpm, intimate 84 bpm). Do NOT default to a fixed 112 bpm.
5. DIVERSE INSTRUMENTATION: Specify 2-3 distinct acoustic, electric, or synth instruments suited to the song's musical soul (e.g. nylon guitar, Rhodes piano, vintage Juno pads, slap bass, resonator guitar) rather than generic drums.

[RULES FOR POSTER IMAGE PROMPT]
1. Create a detailed, aesthetic visual prompt that perfectly matches the {genre} vibe and the lyrics theme.
2. Feature a {vocalist} character or silhouette (or ambient aesthetic if instrumental).
3. Include lighting, color grading, and camera aesthetic details.
4. TYPOGRAPHY INTEGRATION: You MUST include instructions to artistically render the exact song title "{title}" into the image.
5. End with --ar 1:1.

[OUTPUT FORMAT]
You MUST output ONLY a valid JSON object with this exact schema:
{{
  "suno_prompt": "string",
  "poster_prompt": "string"
}}
"""


def generate_track_variant(title: str, lyrics: str, genre: str, vocalist: str) -> Dict[str, Any]:
    from google.genai import types
    from domain.services.prompt_service import build_suno_style_prompt

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
            
            if raw.startswith("```"):
                lines = raw.splitlines()
                raw = "\n".join(
                    line for line in lines if not line.strip().startswith("```")
                ).strip()

            data = json.loads(raw)
            suno_prompt = str(data.get("suno_prompt", "")).strip()
            poster_prompt = str(data.get("poster_prompt", "")).strip()

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

    return {
        "success": False,
        "error": str(last_error),
        "suno_prompt": build_suno_style_prompt(genre, vocalist, creative_concept=lyrics[:300] if lyrics else title),
        "poster_prompt": f"Cinematic album cover for '{title}', {genre} aesthetic, featuring {vocalist.lower()} artist, typography displaying '{title}', dramatic lighting, album art --ar 1:1"
    }


def curate_thematic_vocabulary_batch(
    candidate_nouns: List[str],
    candidate_verbs: List[str],
    candidate_adjs: List[str],
    domain_focus: Optional[str] = None,
    sparks: Optional[Dict[str, Any]] = None,
    target_nouns: int = 10,
    target_verbs: int = 6,
    target_modifiers: int = 4,
    domain_quotas: Optional[Dict[str, Any]] = None,
    candidate_domains: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    from google.genai import types

    nouns_str = ", ".join(candidate_nouns) if candidate_nouns else "None available (0 Nouns target for this song)"
    verbs_str = ", ".join(candidate_verbs) if candidate_verbs else "None"
    adjs_str = ", ".join(candidate_adjs) if candidate_adjs else "None"

    is_specialized = bool(
        domain_focus
        and domain_focus != "All Domains"
        and "الكل" not in domain_focus
        and "All" not in domain_focus
    )

    effective_domain = domain_focus if is_specialized else "Basic / Neutral"
    if sparks is None:
        sparks = sample_domain_creative_sparks(effective_domain)

    domain_instruction = ""
    scenario_instruction = ""
    practicality_guidance = ""

    if is_specialized:
        profile = get_category_profile(domain_focus)
        settings_examples = sparks.get("sampled_settings", [])
        settings_bullets = (
            "\n".join(f"  * {s}" for s in settings_examples)
            if settings_examples
            else f"  * {profile.get('setting', 'Real-world situations in this domain')}"
        )
        conflicts = sparks.get("sampled_conflicts", [])
        conflicts_bullets = (
            "\n".join(f"  * {c}" for c in conflicts)
            if conflicts
            else "  * A realistic human challenge or decision in this field"
        )
        directive = profile.get("domain_directive", "")

        if domain_focus == "Basic / Neutral":
            drift_rule = "- Ground the scenario in authentic everyday life, conversations, and human experiences (embracing both daily warmth and poignant moments of grief, sadness, or quiet goodbyes). Avoid abstract fantasies or overly academic lectures. CREATIVE EXPANSION: Draw from the full landscape of varied human environments across different times of day."
            scenario_instruction = f"""1. SCENARIO FIRST (Anchor the Scene in Everyday Life — INVENT, DO NOT COPY):
   - First, scan the candidate words to discover a concrete, relatable everyday human scenario that connects the highest quality candidates together.
   - FULL EMOTIONAL PALETTE (EMBRACE SADNESS & POIGNANCY): Embrace sad, poignant, melancholic, or heartbreaking everyday moments (e.g. parting ways, hospital clinics, coping with grief, quiet loneliness) just as naturally as daily routines. Sadness is an authentic pillar of everyday human experience.
   - CREATIVE EXPANSION: Explore diverse settings across morning, afternoon, evening, and night — busy morning markets, school pickup lines, sunlit garages, dinner tables, clinics, and highway drives.
   - Use the representative settings, conflict archetypes, and creative sparks below as creative inspiration, but NEVER copy them mechanically! Invent a fresh, believable situation tailored specifically to the words in front of you.
   - Anchor the scene with specific human characters facing a real situation together in natural spoken English."""
            practicality_guidance = f"""- Select words that are foundational, high-utility, and natural in real-life spoken American English.
   - Because these words represent everyday communication, look for natural conversational synergy between them across spoken dialogue, questions, and reactions in both upbeat and poignant emotional contexts.
   - REJECT only words that are archaic, dictionary-definition-only, or impossible to use naturally in conversation without forcing unnatural phrasing or broken rhymes ("من غير ما نحشر كلمة بالعافية")."""
        elif domain_focus == "Emotions & Relationships":
            drift_rule = "- Focus strictly on deeply felt, authentic human connections, emotional crossroads, relationships, family bonds, or poignant solo reflections. Avoid generic office jargon, academic lectures, or trivial domestic chores."
            scenario_instruction = f"""1. SCENARIO FIRST (Anchor the Scene in Real Human Connection — INVENT, DO NOT COPY):
   - First, scan the candidate words to discover a concrete, relatable human scenario within '{domain_focus}' that connects the highest quality candidates together.
   - FULL EMOTIONAL PALETTE (EMBRACE SADNESS, BITTERSWEET TRUTH & SURPRISE): Do not force a neat, happy, tidy resolution on every song! Authentic human relationships experience real grief, painful goodbyes, unfixable distance, and unexpected emotional revelations. Let sadness, longing, and bittersweet truth breathe with dignity and emotional power.
   - STRICT NO-CLOCK OPENING RULE: The scenario and song lyrics must NEVER begin with clock-watching or digital alarm announcements (e.g. 'It is 5:45 AM', '8:30 on the clock'). Begin directly in media res with direct spoken words, physical interaction, sensory atmosphere, or immediate emotional crossroads.
   - DIVERSE RELATIONSHIP DYNAMICS: Explore relationships beyond romantic tropes (estranged siblings, parent and adult child, childhood friends reuniting after years, a solo narrator coping with absence).
   - Anchor the scene with specific human characters facing a real situation together in natural spoken English."""
            practicality_guidance = f"""- Select words that are emotionally authentic, high-utility, and natural in real-life spoken American English.
   - Emotional weight comes from honest, understated spoken lines that real human beings say when vulnerable — not melodramatic greeting-card poetry.
   - REJECT only words that are archaic, dictionary-definition-only, or impossible to use naturally in conversation without forcing unnatural phrasing or broken rhymes ("من غير ما نحشر كلمة بالعافية")."""
        else:
            drift_rule = "- DO NOT drift into generic street arguments, domestic chores, or unrelated casual tropes."
            scenario_instruction = f"""1. SCENARIO FIRST (Anchor the Scene in {domain_focus}):
   - First, scan the candidate words to discover a concrete, relatable human scenario within '{domain_focus}' that connects the highest quality candidates together.
   - Ground the scene in authentic settings and conflict archetypes like those specified above (e.g. lab pressures, code bugs, clinical trials, academic defenses, specialized teamwork, or organizational decisions).
   - Anchor the scene with specific human collaborators facing a real situation together. Avoid vague, detached, or generic storylines."""
            practicality_guidance = f"""- Select words that are useful, frequent, and natural in real-life spoken American English within the '{domain_focus}' context.
   - In specialized professional or academic domains, educated spoken dialogue (lab, collegiate, or tech dialogue) is the intended standard. Do NOT reject words merely because they sound educated, technical, or specialized (e.g. analysis, database, connect, progress, storage, input, specialist). Native speakers use these words constantly in these environments!
   - REJECT only words that are archaic, dictionary-definition-only, or impossible to use naturally in conversation without forcing unnatural phrasing or broken rhymes ("من غير ما نحشر كلمة بالعافية")."""

        domain_instruction = f"""
PRIMARY THEMATIC DOMAIN FOCUS: {domain_focus}
- The user specifically requested a vocabulary batch and story grounded in the '{domain_focus}' domain.
- The curated theme, story concept, and 20 words MUST be firmly situated in this world.
{drift_rule}

DOMAIN DIRECTIVE & REGISTER GUIDANCE (DYNAMIC STORY DESIGN takes precedence over legacy plot/ending suggestions):
{directive}

REPRESENTATIVE REAL-WORLD SETTINGS (Use as inspiration for infinite creative diversity; do NOT repeat blindly):
{settings_bullets}

AUTHENTIC CONFLICT & SCENARIO ARCHETYPES:
{conflicts_bullets}
"""
    else:
        domain_instruction = """
PRIMARY THEMATIC FOCUS:
- Everyday human life, relatable situations, and authentic spoken communication.
"""
        scenario_instruction = """1. SCENARIO FIRST (Anchor the Scene):
   - First, scan the candidate words to discover a concrete, relatable, everyday human scenario that connects the highest quality candidates together (e.g. resolving a misunderstanding with a friend, an overdue late-night conversation, a big career or personal decision, family life).
   - Anchor the scene with specific human characters facing a real situation together."""

        practicality_guidance = """- Select words that are useful, frequent, and natural in real-life spoken American English.
   - REJECT words that are hyper-technical, archaic, or awkward to use in a song without forcing weird rhymes or distorted word order ("من غير ما نحشر كلمة بالعافية")."""

    if domain_focus == "Basic / Neutral":
        balance_guidance = """4. PURE BASIC / NEUTRAL HARMONY:
   - The candidate pool consists of foundational, universal everyday words.
   - Select words that weave effortlessly into real, relatable, spoken English conversations without stiff formality."""
    else:
        balance_guidance = """4. DOMAIN & GENERAL BALANCE:
   - Weave together specialized domain terms with natural universal/neutral words (actions, objects, connectors) so the characters sound like real living human beings interacting in their environment, not an encyclopedia."""

    genres_str = "\n".join(f"- {g}" for g in GENRES)
    structures_str = "\n".join(f"- {s}" for s in SONG_STRUCTURES)
    moods_str = "\n".join(f"- {m}" for m in MOOD_CATEGORIES)

    prompt = f"""You are an elite ESL vocabulary curator, master curriculum director, and hit songwriter for Audingo.

AUDINGO EDUCATIONAL MISSION:
Songs in Audingo are engineered so English language learners can memorize ANY lyric line and use it as natural, authentic spoken English in real life.
The 20 target words must not be a random grab-bag; they must share **exceptional semantic chemistry**, high conversational collocability, and deep natural synergy around a single, relatable slice-of-life scenario.

TASK: From the candidate pools of unused English words below, curate an extraordinarily cohesive batch of EXACTLY 20 target words:
- Exactly {target_nouns} Nouns (chosen ONLY from Candidate Nouns below)
- Exactly {target_verbs} Verbs (chosen ONLY from Candidate Verbs below)
- Exactly {target_modifiers} Modifiers/Adverbs (chosen ONLY from Candidate Modifiers below)
SOURCE MEMBERSHIP CONSTRAINTS (data, not story instructions):
- Required source counts per POS, when supplied: {json.dumps(domain_quotas or {}, ensure_ascii=False)}
- Candidate word to source mapping: {json.dumps(candidate_domains or {}, ensure_ascii=False)}
- Honor these counts while choosing the words AND designing their story. Basic / Neutral always fits the selected domain when used naturally.
{domain_instruction}
Follow the FINAL STORY AUTHORITY below.

Available Genres (all 13 genres pre-curated for ESL vocal clarity):
{genres_str}

Available Song Structures:
{structures_str}

Available Mood Categories (Percentages MUST sum up to exactly 100):
{moods_str}

CANDIDATE NOUNS ({len(candidate_nouns)} available):
{nouns_str}

CANDIDATE VERBS ({len(candidate_verbs)} available):
{verbs_str}

CANDIDATE MODIFIERS (Adverbs / Adjectives) ({len(candidate_adjs)} available):
{adjs_str}

INTELLIGENT SELECTION METHODOLOGY:
{scenario_instruction}

2. HIGH MUTUAL COLLOCABILITY & NATURAL CHEMISTRY:
   - The chosen 20 words must feel like they naturally belong in the same conversation, room, and storyline.
   - When speakers in this setting discuss this scenario, these words naturally roll off the tongue together:
     * Verbs ({target_verbs}): Active, conversational actions the characters actually take or experience in this world. Avoid stiff, robotic, or awkward verbs.
     * Nouns ({target_nouns}): The physical objects, people, locations, data, or emotional stakes in this scene.
     * Modifiers/Adverbs ({target_modifiers}): Relatable emotional states, sensory conditions, nuances, or situational qualities.

3. ESL CONVERSATIONAL PRACTICALITY:
   {practicality_guidance}

{balance_guidance}

5. STRICT MEMBERSHIP & EXACT COUNTS:
   - Every single selected word MUST be chosen verbatim from the candidate lists provided above.
   - Exactly {target_nouns} Nouns, Exactly {target_verbs} Verbs, Exactly {target_modifiers} Modifiers/Adverbs. Total = 20 words.

FINAL STORY AUTHORITY:
{_story_direction(domain_focus or "All Domains")}

6. MUSICAL & EMOTIONAL DIRECTION (ALL-IN-ONE HARMONIZATION):
   - Analyze the emotional core and energy of this curated scenario and the 20 target words.
   - Assign an authentic emotional mood breakdown across Available Mood Categories (percentages summing up to exactly 100).
   - Select the single best matching Genre from Available Genres.
   - Select the single best matching Song Structure from Available Song Structures.

Return a valid JSON object with the following exact schema:
{{
    "theme_name": "A short, catchy, evocative 2-4 word theme name",
    "creative_concept": "A specific, vivid 3-4 sentence narrative scenario explicitly defining characters, concrete setting, core tension, and narrative progression, designed to anchor natural spoken dialogue.",
    "genre": "Exact match from Available Genres",
    "song_structure": "Exact match from Available Song Structures",
    "mood_breakdown": {{
        "Mood Name": 50,
        "Another Mood": 30,
        "Third Mood": 20
    }},
    "selected_nouns": ["noun1", ...],
    "selected_verbs": ["verb1", ...],
    "selected_adjectives": ["mod1", ...]
}}
"""

    from data.services.fallback_engine import generate_with_fallback, CRITIC_FALLBACK_CHAIN

    try:
        raw, model_idx = generate_with_fallback(
            prompt=prompt,
            model_chain=CRITIC_FALLBACK_CHAIN,
            start_index=0,
            require_json=True,
            temperature=0.55,
        )
        data = json.loads(raw)
        model_name = CRITIC_FALLBACK_CHAIN[model_idx]
        concept = data.get("creative_concept") or data.get("theme_description", "")

        genre = data.get("genre", GENRES[0])
        if genre not in GENRES:
            genre = GENRES[0]

        structure = data.get("song_structure", SONG_STRUCTURES[0])
        if structure not in SONG_STRUCTURES:
            structure = SONG_STRUCTURES[0]

        mood_breakdown = data.get("mood_breakdown", {})
        if not mood_breakdown or not isinstance(mood_breakdown, dict):
            mood_breakdown = {}

        selected_nouns = data.get("selected_nouns", candidate_nouns[:target_nouns])
        selected_verbs = data.get("selected_verbs", candidate_verbs[:target_verbs])
        selected_mods = data.get("selected_adjectives") or data.get("selected_modifiers", candidate_adjs[:target_modifiers])

        return {
            "success": True,
            "model_used": model_name,
            "selected_nouns": selected_nouns,
            "selected_verbs": selected_verbs,
            "selected_adjectives": selected_mods,
            "theme_name": data.get("theme_name", "Everyday Life & Human Stories"),
            "theme_description": concept,
            "creative_concept": concept,
            "creative_sparks": sparks,
            "genre": genre,
            "song_structure": structure,
            "mood_breakdown": mood_breakdown,
        }
    except Exception as exc:
        logger.warning("Thematic curation failed: %s", exc)
        profile_def = get_category_profile(domain_focus)
        fallback_story = profile_def.get("default_story", "A deeply human story exploring honest vulnerability and authentic connection.")
        return {
            "success": False,
            "error": str(exc),
            "selected_nouns": candidate_nouns[:target_nouns],
            "selected_verbs": candidate_verbs[:target_verbs],
            "selected_adjectives": candidate_adjs[:target_modifiers],
            "theme_name": f"{domain_focus} & Everyday Stories",
            "theme_description": fallback_story,
            "creative_concept": fallback_story,
            "creative_sparks": sparks,
            "genre": GENRES[0],
            "song_structure": SONG_STRUCTURES[0],
            "mood_breakdown": {},
        }


def build_vocab_story_audit_prompt(words: List[str], story_concept: str, domain: str = "Basic / Neutral") -> str:
    """Build the JSON prompt to audit 20 words against a story concept for natural conversational fit."""
    words_str = ", ".join(f'"{w}"' for w in words)
    profile = get_category_profile(domain)
    directive = profile.get("domain_directive", "")

    return f"""You are an elite ESL songwriting director, master linguist, and curriculum auditor for Audingo.

AUDINGO EDUCATIONAL MISSION & PEDAGOGICAL PHILOSOPHY:
In Audingo, songs are written to help English language learners acquire natural spoken English.
The ultimate standard is:
"An English learner can memorize ANY single line in the song and find that it is a real, authentic sentence that native speakers actually say in their everyday lives."

Therefore, each line in the song must:
1. Sound completely natural, conversational, and unforced (NO strained grammar, inverted syntax, archaic language, or excessive poetic abstraction).
2. Keep a single, orderly, cohesive storyline without disjointed topic leaps.
3. Employ target vocabulary words in their natural, everyday conversational meaning — WITHOUT forcing any word awkwardly into the sentence ("من غير ما نحشر كلمة بالعافية").

INPUT DATA:
- Active Category Domain: "{domain}"
- Domain Directive: {directive}
- Story / Creative Scenario:
\"\"\"
{story_concept}
\"\"\"

- 20 Target Vocabulary Words to Audit:
[{words_str}]

CRITICAL AUDITING PHILOSOPHY: FAIRNESS, REALISTIC DIALOGUE & CONTEXTUAL PLAUSIBILITY (منصف ومحدد في احتمالية التوافق):
1. PRINCIPLE OF FAIRNESS & PLURALITY (الإنصاف والمرونة السياقية):
   - A song is an authentic human narrative and living spoken dialogue, NOT a narrow dictionary article or technical specification.
   - In ANY real-world scene, characters naturally speak about:
     * Physical Setting & Environment: Objects, rooms, weather, time, tools (e.g. table, door, chair, rain, window, car, night, morning).
     * Human Emotions, Attitudes & Reactions: How people feel, wonder, or respond (e.g. fear, hope, tired, proud, doubt, calm, sure).
     * Everyday Actions & Conversational Exchanges: Normal human actions and dialogue (e.g. wait, ask, listen, explain, call, check, step, notice).
     * Common Conversational Idioms: Natural spoken phrases used in daily English.
   - PLAUSIBILITY TEST: If a skilled songwriter can plausibly write a natural, authentic spoken sentence in this scene using the word — whether as spoken dialogue, a description of the scene, an action, or an emotional state — **IT IS A VALID FIT AND MUST PASS! DO NOT FLAG IT!**

2. UNIVERSAL EXEMPTION FOR BASIC / NEUTRAL WORDS:
   - Common, versatile everyday words (e.g. "time", "day", "door", "friend", "water", "walk", "call", "talk", "happy", "look", "car", "wait", "listen", "home", "step", "answer", "mind", "hold", "clear", etc.) naturally fit into virtually ANY human story or conversation.
   - You MUST NEVER flag basic or neutral everyday words as "out of context" or "forced". They are the natural glue of all English communication.

3. DOMAIN-AWARE VALIDITY:
   - For "{domain}" (especially "Science, Tech & Academia" or "Business & Career"): Moderately formal, educated spoken English (e.g., formula, discovery, specialist, strategy, critical, demonstrate, analyze, database, perspective) is COMPLETELY NATURAL in this scene. Do NOT flag these words as "technical alienation" or "formal jargon" when the scene is set in this domain!

4. STRICT HIGH THRESHOLD FOR FLAGGING (ONLY FLAG GENUINE, INSURMOUNTABLE CLASHES):
   - ONLY flag a word if it creates a severe, unbridgeable thematic or stylistic clash that would FORCE the songwriter to invent bizarre, artificial, or distorted sentences.
   - Examples of genuine clashes:
     * Extreme Technical / Domain Alienation: Hyper-specialized jargon (e.g. "photosynthesis", "subpoena", "mitochondria", "amortization") in an intimate emotional scene, casual small talk, or simple street setting where native speakers would never use such terms.
     * Archaic or Obscure Register: Words so formal, stiff, or antiquated that no native speaker would ever utter them in spoken conversational dialogue in this scene.
     * Severe Narrative Incoherence: A word whose literal meaning is completely irreconcilable with the characters, location, or conflict of the story.
   - BENEFIT OF THE DOUBT: If you can imagine even one natural, realistic line of dialogue or setting description in this scene that uses the word naturally, IT PASSES.

5. SPECIFIC & CONSTRUCTIVE FEEDBACK FOR FLAGGED WORDS (محدد ودقيق):
   - For any word genuinely flagged, provide:
     * Precise explanation: 1-2 clear, objective sentences explaining why this word cannot plausibly fit into natural spoken dialogue in this specific scene without sounding strained or artificial.
     * Constructive guidance: Explicitly state whether swapping the word with a fresh unused word is recommended, or if there is a narrow specific angle to make it work.

Return a valid JSON object matching this exact schema:
{{
    "all_fit": true,
    "flagged_words": [
        {{
            "word": "exact_word_from_input",
            "reason": "1-2 specific, objective sentences explaining why this word cannot plausibly fit into natural spoken dialogue in this scene without forcing unnatural language.",
            "suggestion": "Recommendation to swap or narrow context suggestion."
        }}
    ],
    "summary": "1-2 concise, balanced sentences summarizing the thematic coherence and conversational plausibility of the batch."
}}
"""


def audit_words_against_story(words: List[str], story_concept: str, domain: str = "Basic / Neutral") -> Dict[str, Any]:
    """
    Audit 20 target vocabulary words against a story/creative concept.
    Flags words that feel forced, overly technical, or out of context for natural everyday dialogue,
    while exempting basic/neutral words and respecting domain-appropriate vocabulary.
    Uses the same strict 3.8 -> 3.7 -> 3.6 quality chain as thematic selection and criticism.
    """
    from data.services.fallback_engine import generate_with_fallback, CRITIC_FALLBACK_CHAIN

    prompt = build_vocab_story_audit_prompt(words, story_concept, domain=domain)

    try:
        raw, model_idx = generate_with_fallback(
            prompt=prompt,
            model_chain=CRITIC_FALLBACK_CHAIN,
            start_index=0,
            require_json=True,
            temperature=0.3,
        )
        data = json.loads(raw)
        model_name = CRITIC_FALLBACK_CHAIN[model_idx]
        flagged = data.get("flagged_words", [])
        all_fit = data.get("all_fit", len(flagged) == 0)

        return {
            "success": True,
            "model_used": model_name,
            "all_fit": all_fit and len(flagged) == 0,
            "flagged_words": flagged,
            "summary": data.get(
                "summary",
                "All words fit the scenario naturally." if not flagged else f"{len(flagged)} word(s) flagged."
            )
        }
    except Exception as exc:
        logger.warning("Vocab-story audit failed: %s", exc)
        return {
            "success": False,
            "error": str(exc),
            "all_fit": True,
            "flagged_words": [],
            "summary": "Could not complete audit due to service error."
        }
