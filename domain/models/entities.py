from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

@dataclass
class NgslWord:
    id: Optional[int]
    word: str
    lemma_family: str
    pos_type: str
    usage_count: int = 0
    domain: Optional[str] = None

@dataclass
class ExtraWord:
    id: Optional[int]
    word: str
    occurrence_count: int = 1
    first_seen_in_song: Optional[str] = None

@dataclass
class Song:
    id: Optional[int]
    title: str
    lyrics: str
    target_words: str  # Could be JSON string or List[str] if handled by repo
    bonus_words: Optional[str] = None
    extra_words: Optional[str] = None
    mood_breakdown: Optional[str] = None
    genre: Optional[str] = None
    song_structure: Optional[str] = None
    creative_concept: Optional[str] = None
    reused_words: Optional[str] = None
    created_at: Optional[datetime] = None

    @property
    def target_words_list(self) -> List[str]:
        if not self.target_words: return []
        try:
            return json.loads(self.target_words)
        except json.JSONDecodeError:
            return [w.strip() for w in self.target_words.split(',')]

    @property
    def bonus_words_list(self) -> List[str]:
        if not self.bonus_words: return []
        try:
            return json.loads(self.bonus_words)
        except json.JSONDecodeError:
            return [w.strip() for w in self.bonus_words.split(',')]

@dataclass
class TrackVariant:
    id: Optional[int]
    song_id: int
    genre: str
    vocalist: str
    suno_prompt: str
    poster_prompt: str
    created_at: Optional[datetime] = None

@dataclass
class PosterPrompt:
    id: Optional[int]
    song_id: int
    genre: str
    vocalist: str
    prompt_text: str
    created_at: Optional[datetime] = None

@dataclass
class StudioDraft:
    id: Optional[int]
    song_title: str
    label: str
    session_json: str
    saved_at: Optional[datetime] = None

    @property
    def session_data(self) -> Dict[str, Any]:
        return json.loads(self.session_json) if self.session_json else {}

@dataclass
class AppState:
    key: str
    value: str
