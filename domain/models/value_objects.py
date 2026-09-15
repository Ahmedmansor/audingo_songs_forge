"""
value_objects.py — Domain Value Objects & Data Structures.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass(frozen=True)
class VocabularyStats:
    total: int
    used: int
    unused: int
    percent: float


@dataclass(frozen=True)
class LyricsClassification:
    target_hits: List[str]       # Green: in target batch & lyrics
    missed_targets: List[str]    # Red: in target batch but missed
    bonus_ngsl_hits: List[str]   # Blue: in NGSL, not in target, usage_count == 0
    reused_ngsl_hits: List[str]  # Reused: in NGSL, not in target, usage_count > 0
    extra_words: List[str]       # Yellow: non-NGSL, non-stopword, non-proper noun


@dataclass
class DomainBreakdown:
    total_words: int
    domains: Dict[str, Dict[str, Any]]
    primary_domain: str
    primary_percent: float
    is_high_formal: bool
    formal_percent: float


@dataclass
class VocabularyBatch:
    words: List[Dict[str, Any]]
    domain_focus: Optional[str] = None
    
    @property
    def word_strings(self) -> List[str]:
        return [w["word"] for w in self.words]
        
    @property
    def nouns(self) -> List[Dict[str, Any]]:
        return [w for w in self.words if w.get("pos_type") == "Noun"]

    @property
    def verbs(self) -> List[Dict[str, Any]]:
        return [w for w in self.words if w.get("pos_type") == "Verb"]

    @property
    def adjectives(self) -> List[Dict[str, Any]]:
        return [w for w in self.words if w.get("pos_type") == "Adjective"]
