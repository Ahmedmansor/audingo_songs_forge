import unittest
from domain.services.prompt_service import (
    build_suno_style_prompt,
    detect_emotional_tone,
    SUNO_GENRE_TONE_PALETTES,
)

class SunoToneAdaptationTests(unittest.TestCase):
    def test_detect_emotional_tone_from_breakdown(self):
        sad_mood = {"Sad / Heartbroken": 80, "Nostalgic / Melancholic": 20}
        self.assertEqual(detect_emotional_tone(sad_mood), "melancholic")

        happy_mood = {"Happy": 70, "Energetic": 30}
        self.assertEqual(detect_emotional_tone(happy_mood), "energetic")

        romantic_mood = {"Romantic / Sweet": 90}
        self.assertEqual(detect_emotional_tone(romantic_mood), "romantic")

        chill_mood = {"Chill / Relaxed": 85}
        self.assertEqual(detect_emotional_tone(chill_mood), "chill")

    def test_sad_song_gets_slow_tempo_and_emotive_palette(self):
        prompt = build_suno_style_prompt(
            genre="Pop",
            vocalist="Male",
            mood_analysis={"Sad / Heartbroken": 90},
            creative_concept="Saying goodbye in tears at the airport."
        )
        self.assertLessEqual(len(prompt), 120)
        # Should NOT contain high-energy party dance elements
        self.assertNotIn("Dance-pop", prompt)
        self.assertNotIn("bouncy 124 bpm", prompt)
        self.assertNotIn("high-energy", prompt)
        # Should have slow/intimate tempo (under 95 bpm)
        self.assertTrue(any(t in prompt for t in ["74 bpm", "80 bpm", "86 bpm", "90 bpm"]))

    def test_happy_song_gets_upbeat_tempo(self):
        prompt = build_suno_style_prompt(
            genre="Pop",
            vocalist="Female",
            mood_analysis={"Happy": 80, "Energetic": 20},
            creative_concept="Celebrating a victory at the party with laughing friends."
        )
        self.assertLessEqual(len(prompt), 120)
        # Should have upbeat tempo (116+ bpm)
        self.assertTrue(any(t in prompt for t in ["116 bpm", "120 bpm", "124 bpm", "128 bpm"]))

    def test_all_genres_and_tones_strictly_under_120_chars(self):
        tones = [
            {"Sad / Heartbroken": 100},
            {"Happy": 100},
            {"Romantic / Sweet": 100},
            {"Chill / Relaxed": 100},
            {"Dark / Moody": 100},
            {"Uplifting / Inspiring": 100},
        ]
        for genre in SUNO_GENRE_TONE_PALETTES.keys():
            for mood in tones:
                prompt = build_suno_style_prompt(genre, "Male", mood_analysis=mood)
                self.assertLessEqual(
                    len(prompt),
                    120,
                    f"Prompt exceeded 120 chars for {genre} with mood {mood}: '{prompt}'"
                )

if __name__ == "__main__":
    unittest.main()
