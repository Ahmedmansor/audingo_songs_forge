"""
metadata_gen.py — Gemini API integration for YouTube Shorts metadata.

Makes ONE API call per language (4 total), sleeping GEMINI_RPM_SLEEP seconds
between each call to respect the free-tier 5 RPM rate limit.

Output schema per language:
{
    "title":       "Punchy title #Shorts",        # max ~100 chars, ends with #Shorts
    "description": "Teaser text...\n\n#Shorts",   # contains #Shorts hashtag
    "tags":        ["tag1", "tag2", ...]           # 10-15 items, no '#' prefix
}
"""

import json
import logging
import os
import tempfile
import time
from pathlib import Path

from google import genai
from google.genai import types
from dotenv import load_dotenv

from config import (
    GEMINI_MODEL,
    GEMINI_RPM_SLEEP,
    LANGUAGE_CONTEXTS,
    LANGUAGES,
    SHOW_NAME,
    VIDEO_TAGS,
    HASHTAGS,
    DISCLAIMERS,
)

load_dotenv()
logger = logging.getLogger(__name__)

METADATA_CACHE_FILENAME = "metadata.json"


# ─── Cache Helpers ───────────────────────────────────────────────────────────

def _load_cache(episode_path: Path) -> dict:
    """
    Load the per-episode metadata cache from metadata.json.
    Returns an empty dict if the file is missing or corrupt.
    """
    cache_file = episode_path / METADATA_CACHE_FILENAME
    if not cache_file.exists():
        return {}
    try:
        with cache_file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        logger.debug("Loaded metadata cache from %s", cache_file)
        return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning(
            "Could not read metadata cache %s (%s) — starting fresh.", cache_file, exc
        )
        return {}


def _save_cache(episode_path: Path, cache: dict) -> None:
    """
    Atomically write the updated metadata cache to metadata.json using a
    temp-file-then-rename strategy (same pattern as state_manager.py).
    """
    cache_file = episode_path / METADATA_CACHE_FILENAME
    fd, tmp_path = tempfile.mkstemp(
        dir=episode_path, suffix=".tmp", prefix="meta_"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(cache, fh, ensure_ascii=False, indent=2)
        os.replace(tmp_path, cache_file)
        logger.debug("Metadata cache saved → %s", cache_file)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _is_cache_valid(entry: object) -> bool:
    """Return True only if a cache entry contains all three required keys."""
    return (
        isinstance(entry, dict)
        and all(k in entry for k in ("title", "description", "tags"))
    )


# ─── Prompt Builder ───────────────────────────────────────────────────────────

def _build_prompt(script_text: str, lang: str) -> str:
    """Build the full Gemini prompt for a specific language."""
    ctx = LANGUAGE_CONTEXTS[lang]
    return f"""You are a funny, sarcastic friend telling a "Saye3" (street-smart) story about \
the show "{SHOW_NAME}". Your vibe is high energy, viral-focused, and click-baity.

SHOW: "{SHOW_NAME}"
CHANNEL NOTE: {ctx['channel_note']}
TARGET AUDIENCE: {ctx['audience']}
REQUIRED TONE: {ctx['tone']}

SOURCE SCRIPT (the full episode recap — may be written in Arabic):
---
{script_text.strip()}
---

LANGUAGE & TONE INSTRUCTIONS:
- If translating/writing in Arabic (AR): STRICTLY PROHIBIT Modern Standard Arabic (Fusha). You MUST use Egyptian Street Slang (EG-AMMIYA). Use natural street terms like "هبدة", "لبس في الحيط", "لقطة صايعة", "روشنة", etc.
- If translating/writing in Global languages ({ctx['language_name']} / {ctx['language_native']}): Use A1/A2 basic, energetic, everyday street language. It must be universally understood but keep the hilarious "funny friend" vibe.

SMART TITLE LOGIC:
1. PRIORITIZE THE HUMAN HOOK: Specifically look at the very FIRST sentence of the script. If it is relatable, conversational, or sounds like a personal interview/story hook, you MUST use it as the main inspiration for your title.
2. Only if the first sentence is completely boring or irrelevant, you can look for a "Viral" or "Chaotic" moment later in the script (like a massive fail or crazy plot twist) to use instead!

OUTPUT RULES:

TITLE:
- Write in {ctx['language_name']} ({ctx['language_native']}).
- IF the target language is English: Make the title MUCH MORE AGGRESSIVE, SARCASTIC, and FUNNY! Don't hold back, use edgy roasting energy.
- MAXIMUM 60 characters (not counting the ' #Shorts' suffix).
- MUST end with the exact literal string ' #Shorts' (one space before the hash).
- Must be dramatic, funny, and curiosity-driven (optimised for Shorts click-through rate).
- Do NOT start with "Episode", "Ep", or "Recap". No quotation marks around the title.

DESCRIPTION:
- Write in {ctx['language_name']} ({ctx['language_native']}).
- MUST start with a funny "Hook" sentence, followed by a punchy summary of the chaos.
- 3 to 5 lines maximum.
- Do NOT include any hashtags in the description. They will be injected automatically later.

CRITICAL: Respond with ONLY a valid JSON object — no markdown fences, no prose,
no explanation outside the JSON. Exact schema required:
{{
  "title": "string",
  "description": "string"
}}"""


# ─── Client Initialisation ─────────────────────────────────────────────────

def _init_client() -> genai.Client:
    """Create and return an authenticated google-genai Client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. "
            "Copy .env.example → .env and add your real key."
        )
    return genai.Client(api_key=api_key)


# ─── Single API Call ─────────────────────────────────────────────────────────

def _call_gemini(client: genai.Client, prompt: str, lang: str) -> dict | None:
    """
    Execute one Gemini API call using the new google-genai SDK and return the
    validated/normalised metadata dict. Returns None on any failure.
    Includes a retry mechanism for transient server errors (e.g., 503 UNAVAILABLE).
    """
    max_retries = 6  # Will try 6 times total
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.85,
                ),
            )
            raw = response.text.strip()

            # Strip accidental markdown fences Gemini sometimes adds
            if raw.startswith("```"):
                lines = raw.splitlines()
                raw = "\n".join(
                    line for line in lines
                    if not line.strip().startswith("```")
                ).strip()

            data = json.loads(raw)

            # Validate required keys
            for key in ("title", "description"):
                if key not in data:
                    raise ValueError(f"Missing key '{key}' in Gemini JSON response.")

            # ── Enforce #Shorts at end of title ───────────────────────────────────
            title = data["title"].rstrip()
            if not title.endswith("#Shorts"):
                title = title.rstrip() + " #Shorts"
            data["title"] = title

            # ── Clean up description and inject disclaimers/hashtags ─────────────
            desc = data["description"].strip()
            # Remove any stray #Shorts that might have been generated
            desc = desc.replace("#Shorts", "").replace("#shorts", "").strip()
            
            # Inject the Disclaimer and Hashtags
            disclaimer = DISCLAIMERS.get(lang, "")
            hashtags = HASHTAGS.get(lang, "")
            
            final_desc = f"{desc}\n\n{disclaimer}\n\n{hashtags}"
            data["description"] = final_desc

            # ── Inject static tags ───────────────────────────────────────────────
            data["tags"] = VIDEO_TAGS.get(lang, [])

            logger.info("[%s] ✓ Metadata OK — Title: %s", lang, data["title"])
            return data

        except json.JSONDecodeError as exc:
            logger.error("[%s] Gemini returned invalid JSON: %s", lang, exc)
            return None
        except ValueError as exc:
            logger.error("[%s] Gemini schema error: %s", lang, exc)
            return None
        except Exception as exc:
            err_str = str(exc)
            # Check for common transient/rate-limiting errors
            is_transient = any(code in err_str for code in ["503", "429", "UNAVAILABLE", "Too Many Requests"])
            
            if is_transient and attempt < max_retries - 1:
                wait_time = 15
                logger.warning(
                    "[%s] Gemini Server Busy/Error (Attempt %d/%d). Retrying in %ds...",
                    lang, attempt + 1, max_retries, wait_time
                )
                time.sleep(wait_time)
                continue
                
            logger.error("[%s] Gemini API call failed: %s", lang, exc)
            return None

    return None


# ─── Public Entry Point ───────────────────────────────────────────────────────────

def generate_all_metadata(
    script_text: str,
    episode_path: Path,
    langs: list[str] | None = None,
) -> dict[str, dict | None]:
    """
    Generate YouTube Shorts metadata for each language, with per-language caching.

    Flow for each language:
      1. Check episode_path/metadata.json for a pre-existing valid entry.
         → If found:  use cache, skip the API call entirely.
         → If absent: call Gemini, then immediately persist the result to cache.
    Between consecutive API calls, sleep GEMINI_RPM_SLEEP seconds to respect
    the free-tier 5 RPM rate limit.

    Args:
        script_text:   Full contents of the episode's script.txt file.
        episode_path:  Path to the episode folder (e.g. Upload_Queue/Ep_01/).
                       metadata.json is read from / written to this directory.
        langs:         Language codes to process. Defaults to all LANGUAGES.

    Returns:
        Dict keyed by language code. Value is a metadata dict or None on failure.
        {
            "AR": {"title": "...", "description": "...", "tags": [...]},
            "EN": None,   # API call failed
        }
    """
    if langs is None:
        langs = LANGUAGES

    if not script_text.strip():
        raise ValueError("script_text is empty — cannot generate metadata.")

    # Load existing cache (may already have some languages from a previous run)
    cache = _load_cache(episode_path)

    results: dict[str, dict | None] = {}
    langs_needing_api: list[str] = []

    # ── Separate cached from uncached ───────────────────────────────────────────
    for lang in langs:
        if _is_cache_valid(cache.get(lang)):
            logger.info(
                "[%s] ✓ Using cached metadata — Gemini call skipped.", lang
            )
            results[lang] = cache[lang]
        else:
            langs_needing_api.append(lang)

    if not langs_needing_api:
        logger.info("All languages served from cache. No API calls needed.")
        return results

    # ── Make API calls for uncached languages ────────────────────────────────
    client = _init_client()

    for idx, lang in enumerate(langs_needing_api):
        logger.info(
            "Calling Gemini for [%s] (%d / %d uncached)…",
            lang, idx + 1, len(langs_needing_api),
        )
        prompt = _build_prompt(script_text, lang)
        result = _call_gemini(client, prompt, lang)
        results[lang] = result

        # Persist immediately so a crash during a later upload doesn't lose this
        if result is not None:
            cache[lang] = result
            _save_cache(episode_path, cache)

        # Sleep between API calls — skip after the very last one
        if idx < len(langs_needing_api) - 1:
            logger.debug(
                "Sleeping %ds between calls (rate-limit guard)…", GEMINI_RPM_SLEEP
            )
            time.sleep(GEMINI_RPM_SLEEP)

    success_count = sum(1 for v in results.values() if v is not None)
    logger.info(
        "Metadata generation complete: %d / %d languages successful.",
        success_count, len(langs),
    )
    return results
