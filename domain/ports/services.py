from abc import ABC, abstractmethod
from typing import Dict, Any

class LLMClientInterface(ABC):
    @abstractmethod
    def generate_song(self, prompt: str) -> Dict[str, Any]:
        """
        Should return a dictionary containing the generated song attributes
        like 'title', 'lyrics', 'mood_breakdown', 'creative_concept', etc.
        """
        pass
        
    @abstractmethod
    def get_track_variants(self, song_concept: str, genre: str, vocalist: str) -> Dict[str, str]:
        """
        Should return a dictionary containing 'suno_prompt' and 'poster_prompt'.
        """
        pass
