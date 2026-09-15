"""
lyrics_service.py — Text cleaning and 5-category vocabulary classification service.
"""

import re
import string
from typing import Dict, List, Set, Any, Optional
import contractions
from domain.models.value_objects import LyricsClassification


def clean_lyrics_text(raw_lyrics: str) -> str:
    """
    1. Expand standard contractions without mangling real words (slang=False).
    2. Strip structural markup like [Verse], [Chorus] and section cues like (Chorus).
    3. Isolate punctuation and delimiters to ensure words aren't merged.
    4. Deduplicate repeated lines.
    """
    if not raw_lyrics:
        return ""

    text = (
        raw_lyrics
        .replace('’', "'")
        .replace('‘', "'")
        .replace('`', "'")
        .replace('´', "'")
        .replace('“', '"')
        .replace('”', '"')
    )

    expanded = contractions.fix(text, slang=False)
    cleaned = re.sub(r'\[.*?\]', ' ', expanded)

    tag_pattern = r'\s*\(\s*(?:verse|chorus|bridge|intro|outro|pre-chorus|hook|solo|instrumental|interlude|drop|break|refrain|spoken|whisper|ad-lib|repeat)[\s\d:.-]*\)\s*'
    cleaned = re.sub(tag_pattern, ' ', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'[\(\)\u2014\u2013\u2026/_\\]', ' ', cleaned)

    lines = cleaned.splitlines()
    seen_lines: Set[str] = set()
    unique_lines: List[str] = []

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue
        normalized_line = re.sub(r'[^\w\s]', '', stripped_line.lower())
        if normalized_line and normalized_line not in seen_lines:
            seen_lines.add(normalized_line)
            unique_lines.append(stripped_line)

    return "\n".join(unique_lines)


def process_song_text(
    raw_lyrics: str,
    target_words: List[str],
    lemma_to_headword: Dict[str, str],
    nlp,
    used_ngsl_words: Optional[Set[str]] = None
) -> Dict[str, Any]:
    """
    Execute full pipeline and classify words into 5 categories:
    - green: Target Hit
    - red: Missed Target
    - blue: Bonus NGSL Hit (usage_count == 0)
    - reused: Previously Covered NGSL (usage_count > 0)
    - yellow: Extra Word
    """
    cleaned_text = clean_lyrics_text(raw_lyrics)
    if not cleaned_text.strip():
        return {
            "green": [],
            "red": sorted(list(set(w.lower() for w in target_words))),
            "blue": [],
            "reused": [],
            "yellow": []
        }

    doc = nlp(cleaned_text)

    proper_noun_texts: Set[str] = set()
    for ent in doc.ents:
        if ent.label_ in ("PERSON", "GPE", "LOC", "ORG", "FAC", "NORP"):
            for token in ent:
                proper_noun_texts.add(token.text.lower())
    for token in doc:
        if token.pos_ == "PROPN":
            proper_noun_texts.add(token.text.lower())

    target_set = {w.lower().strip() for w in target_words if w.strip()}

    matched_target_words: Set[str] = set()
    matched_ngsl_headwords: Set[str] = set()
    candidate_extra_words: Set[str] = set()

    for token in doc:
        raw_word = token.text.strip(string.punctuation + "“”‘’…—–").lower()
        lemma_word = token.lemma_.strip(string.punctuation + "“”‘’…—–").lower()

        if not raw_word or len(raw_word) <= 1 or not raw_word.isalpha():
            continue

        if raw_word in target_set:
            matched_target_words.add(raw_word)
        if lemma_word in target_set:
            matched_target_words.add(lemma_word)

        is_proper_noun = (
            token.pos_ == "PROPN"
            or raw_word in proper_noun_texts
            or lemma_word in proper_noun_texts
        )
        if is_proper_noun and raw_word not in target_set and lemma_word not in target_set:
            continue

        if token.is_stop and raw_word not in target_set and lemma_word not in target_set:
            continue

        matched_headword = None
        if lemma_word in lemma_to_headword:
            matched_headword = lemma_to_headword[lemma_word]
        elif raw_word in lemma_to_headword:
            matched_headword = lemma_to_headword[raw_word]

        if matched_headword:
            matched_ngsl_headwords.add(matched_headword)
            if matched_headword in target_set:
                matched_target_words.add(matched_headword)
        else:
            candidate_extra_words.add(lemma_word)

    used_set = {w.lower().strip() for w in used_ngsl_words} if used_ngsl_words else set()

    green_words = sorted(list(matched_target_words.union(target_set.intersection(matched_ngsl_headwords))))
    red_words = sorted(list(target_set.difference(green_words)))
    non_target_ngsl = matched_ngsl_headwords.difference(target_set)
    blue_words = sorted(list(w for w in non_target_ngsl if w not in used_set))
    reused_words = sorted(list(w for w in non_target_ngsl if w in used_set))
    yellow_words = sorted(list(candidate_extra_words))

    return {
        "green": green_words,
        "red": red_words,
        "blue": blue_words,
        "reused": reused_words,
        "yellow": yellow_words
    }
