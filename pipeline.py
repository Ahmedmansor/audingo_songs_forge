"""
pipeline.py — Song text processing and vocabulary classification pipeline.
"""

import re
import string
from typing import Dict, List, Set, Any, Tuple
import contractions


def clean_lyrics_text(raw_lyrics: str) -> str:
    """
    Step 1 & 2:
    1. Expand contractions (e.g. don't -> do not).
    2. Strip structural markup [Chorus], [Verse], etc., remove punctuation,
       and eliminate duplicate lines caused by repetition/rhyme.
    """
    if not raw_lyrics:
        return ""

    # Step 1: Expand contractions
    expanded = contractions.fix(raw_lyrics)

    # Step 2: Strip structural tags like [Verse 1], [Chorus], (Bridge), etc.
    cleaned_no_tags = re.sub(r'\[.*?\]', ' ', expanded)
    cleaned_no_tags = re.sub(r'\(.*?\)', ' ', cleaned_no_tags)

    # Split into lines and deduplicate repetitive lines while preserving flow
    lines = cleaned_no_tags.splitlines()
    seen_lines: Set[str] = set()
    unique_lines: List[str] = []
    
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue
        
        # Normalize line to check for duplicates
        normalized_line = re.sub(r'[^\w\s]', '', stripped_line.lower())
        if normalized_line and normalized_line not in seen_lines:
            seen_lines.add(normalized_line)
            unique_lines.append(stripped_line)

    return "\n".join(unique_lines)


def process_song_text(
    raw_lyrics: str,
    target_words: List[str],
    lemma_to_headword: Dict[str, str],
    nlp
) -> Dict[str, Any]:
    """
    Execute full pipeline:
    1. Expand contractions
    2. Strip structural tags, punctuation, duplicate lines
    3. Filter proper nouns (NER / POS)
    4. Filter stop words
    5. Lemmatize and classify into 4 categories:
       - Green: Target Hit
       - Red: Missed Target
       - Blue: Bonus NGSL Hit
       - Yellow: Extra Word
    """
    cleaned_text = clean_lyrics_text(raw_lyrics)
    if not cleaned_text.strip():
        # Everything in target is missed
        return {
            "green": [],
            "red": sorted(list(set(w.lower() for w in target_words))),
            "blue": [],
            "yellow": []
        }

    # Run spaCy NLP doc
    doc = nlp(cleaned_text)

    # Collect proper noun tokens/spans to exclude from extra_words
    proper_noun_texts: Set[str] = set()
    for ent in doc.ents:
        if ent.label_ in ("PERSON", "GPE", "LOC", "ORG", "FAC", "NORP"):
            for token in ent:
                proper_noun_texts.add(token.text.lower())
    for token in doc:
        if token.pos_ == "PROPN":
            proper_noun_texts.add(token.text.lower())

    # Map target words to lowercase set
    target_set = {w.lower().strip() for w in target_words if w.strip()}

    matched_ngsl_headwords: Set[str] = set()
    candidate_extra_words: Set[str] = set()

    for token in doc:
        # Check basic validity
        if not token.is_alpha or len(token.text) <= 1:
            continue

        raw_word = token.text.lower()
        lemma_word = token.lemma_.lower()

        # Step 3: Filter out proper nouns (people, places, organizations)
        # Proper nouns should never be added to extra_words or counted as bonus hits
        is_proper_noun = (
            token.pos_ == "PROPN"
            or raw_word in proper_noun_texts
            or lemma_word in proper_noun_texts
        )
        if is_proper_noun and raw_word not in target_set and lemma_word not in target_set:
            continue

        # Step 4: Remove stop words (pronouns, prepositions, articles, auxiliary verbs, etc.)
        if token.is_stop and raw_word not in target_set and lemma_word not in target_set:
            continue

        # Step 5: Lemmatize all remaining words back to base form for matching against ngsl_words.lemma_family
        matched_headword = None
        if lemma_word in lemma_to_headword:
            matched_headword = lemma_to_headword[lemma_word]
        elif raw_word in lemma_to_headword:
            matched_headword = lemma_to_headword[raw_word]

        if matched_headword:
            matched_ngsl_headwords.add(matched_headword)
        else:
            # Valid word not in NGSL at all (and already passed proper-noun & stop-word filters)
            candidate_extra_words.add(lemma_word)


    # 4 Classification Categories:
    # 🟢 Green: Target Hit
    green_words = sorted(list(target_set.intersection(matched_ngsl_headwords)))

    # 🔴 Red: Missed Target
    red_words = sorted(list(target_set.difference(matched_ngsl_headwords)))

    # 🔵 Blue: Bonus NGSL Hit (in NGSL but not in target batch)
    blue_words = sorted(list(matched_ngsl_headwords.difference(target_set)))

    # 🟡 Yellow: Extra Word (not in NGSL at all, not proper noun, not stop word)
    yellow_words = sorted(list(candidate_extra_words))

    return {
        "green": green_words,
        "red": red_words,
        "blue": blue_words,
        "yellow": yellow_words
    }
