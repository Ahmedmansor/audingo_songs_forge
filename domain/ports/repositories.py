from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
from domain.models.entities import (
    NgslWord, ExtraWord, Song, TrackVariant, PosterPrompt, StudioDraft, AppState
)
import pandas as pd

class SongRepository(ABC):
    @abstractmethod
    def save_song(self, song: Song) -> Song:
        pass
    
    @abstractmethod
    def get_all_songs(self) -> pd.DataFrame:
        pass
        
    @abstractmethod
    def get_song(self, song_id: int) -> Optional[Song]:
        pass
        
    @abstractmethod
    def update_song(self, song: Song) -> bool:
        pass
        
    @abstractmethod
    def delete_song(self, song_id: int, rollback_words: bool = True) -> bool:
        pass

class WordRepository(ABC):
    @abstractmethod
    def get_all_ngsl_words(self) -> pd.DataFrame:
        pass
        
    @abstractmethod
    def get_extra_words(self) -> pd.DataFrame:
        pass
        
    @abstractmethod
    def update_word_usage(self, words: List[str], count_increment: int) -> None:
        pass
        
    @abstractmethod
    def get_used_ngsl_words(self) -> Set[str]:
        pass

    @abstractmethod
    def get_words_domains(self, words: List[str]) -> Dict[str, str]:
        pass

class TrackVariantRepository(ABC):
    @abstractmethod
    def upsert_variant(self, variant: TrackVariant) -> None:
        pass
        
    @abstractmethod
    def get_variants_for_song(self, song_id: int) -> List[TrackVariant]:
        pass
        
    @abstractmethod
    def delete_variant(self, variant_id: int) -> bool:
        pass

class PosterPromptRepository(ABC):
    @abstractmethod
    def upsert_prompt(self, prompt: PosterPrompt) -> None:
        pass
        
    @abstractmethod
    def get_prompts_for_song(self, song_id: int) -> List[PosterPrompt]:
        pass

class StudioDraftRepository(ABC):
    @abstractmethod
    def save_draft(self, draft: StudioDraft) -> None:
        pass
        
    @abstractmethod
    def list_drafts(self) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def get_draft(self, draft_id: int) -> Optional[StudioDraft]:
        pass
        
    @abstractmethod
    def delete_draft(self, draft_id: int) -> bool:
        pass

class AppStateRepository(ABC):
    @abstractmethod
    def save_state(self, key: str, value: Any) -> None:
        pass
        
    @abstractmethod
    def get_state(self, key: str) -> Optional[Any]:
        pass
        
    @abstractmethod
    def clear_state(self) -> None:
        pass
