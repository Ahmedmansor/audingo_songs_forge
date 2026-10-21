"""
prompt_service.py — Constructs Suno AI style prompts and Master Prompts for external LLMs.
"""

from typing import List, Dict, Any, Optional
import json
import random
import re
from constants import get_category_profile

# Legacy presets retained for backwards compatibility
SUNO_GENRE_PRESETS = {
    "Pop": "Pop, steady 116 bpm, clear upfront {voc} vocals, bright acoustic guitar, modern synth, clean punchy mix",
    "K-Pop Style (Clear English Vocals)": "K-Pop, steady 118 bpm, clear upfront {voc} vocals, punchy synth bass, crisp percussion, clean modern mix",
    "Synth-Pop / 80s Retro": "Synthwave, 80s synth-pop, steady 112 bpm, clear upfront {voc} vocals, warm analog synths, pulsing bass, clean mix",
    "Indie Pop": "Indie pop, steady 114 bpm, clear upfront {voc} vocals, warm acoustic guitar, melodic bassline, clean airy mix",
    "Acoustic / Folk": "Acoustic folk, steady 110 bpm, clear upfront {voc} vocals, acoustic guitar, subtle strings, clean natural mix",
    "R&B / Contemporary Soul": "Contemporary R&B, soul groove, steady 110 bpm, clear upfront {voc} vocals, electric piano, warm bass, clean mix",
    "Country / Americana": "Americana, modern country, steady 112 bpm, clear upfront {voc} vocals, acoustic strumming, pedal steel, clean mix",
    "Funk / Disco Groove": "Disco funk groove, steady 116 bpm, clear upfront {voc} vocals, rhythmic bassline, clean electric guitar, clean mix",
    "Reggae / Tropical Pop": "Tropical reggae pop, steady 110 bpm, clear upfront {voc} vocals, island guitar skank, warm bass, clean mix",
    "Jazz / Bossa Nova": "Bossa nova, smooth jazz, steady 110 bpm, clear upfront {voc} vocals, nylon acoustic guitar, upright bass, clean mix",
    "Cinematic / Ballad": "Cinematic ballad, steady 110 bpm, clear upfront {voc} vocals, emotive grand piano, lush strings, soft intimate verses, building dynamics, powerful chorus, clean dynamic mix",
    "Lo-Fi / Chillhop": "Lo-fi chillhop, steady 110 bpm, clear upfront {voc} vocals, mellow electric piano, relaxed bass, clean vinyl mix",
    "Melodic Chill Electronic": "Melodic chill electronic, steady 112 bpm, clear upfront {voc} vocals, soft piano, warm ambient pads, clean mix",
}

def detect_emotional_tone(
    mood_analysis: Optional[Dict[str, Any]] = None,
    creative_concept: str = ""
) -> str:
    """
    Detects the dominant emotional tone from mood breakdown or story concept.
    Returns one of: 'melancholic', 'energetic', 'romantic', 'dramatic', 'chill', 'uplifting', or 'balanced'.
    """
    scores = {
        'melancholic': 0.0,
        'energetic': 0.0,
        'romantic': 0.0,
        'dramatic': 0.0,
        'chill': 0.0,
        'uplifting': 0.0,
    }

    if isinstance(mood_analysis, dict):
        bd = mood_analysis.get('mood_breakdown', mood_analysis)
        if isinstance(bd, dict):
            scores['melancholic'] += float(bd.get('Sad / Heartbroken', 0)) * 1.6
            scores['melancholic'] += float(bd.get('Nostalgic / Melancholic', 0)) * 1.2
            scores['energetic'] += float(bd.get('Happy', 0)) * 1.0
            scores['energetic'] += float(bd.get('Energetic', 0)) * 1.4
            scores['energetic'] += float(bd.get('Playful / Quirky', 0)) * 1.1
            scores['romantic'] += float(bd.get('Romantic / Sweet', 0)) * 1.5
            scores['dramatic'] += float(bd.get('Dark / Moody', 0)) * 1.3
            scores['dramatic'] += float(bd.get('Dramatic / Intense', 0)) * 1.4
            scores['chill'] += float(bd.get('Chill / Relaxed', 0)) * 1.3
            scores['uplifting'] += float(bd.get('Uplifting / Inspiring', 0)) * 1.2

    c_lower = (creative_concept or "").lower()
    sad_words = ['goodbye', 'tears', 'crying', 'cry', 'loss', 'lost', 'grief', 'funeral', 'heartbreak', 'broken', 'sorrow', 'miss', 'missing', 'lonely', 'alone', 'regret', 'pain', 'depart', 'separate']
    happy_words = ['party', 'celebrate', 'dance', 'laugh', 'laughing', 'joy', 'win', 'winning', 'champion', 'cheer', 'triumph', 'smile', 'smiling']
    romantic_words = ['love', 'romantic', 'kiss', 'holding hands', 'confess', 'sweetheart', 'wedding', 'date', 'candlelit', 'tender', 'affection', 'darling']
    dramatic_words = ['danger', 'threat', 'fight', 'argument', 'storm', 'chase', 'crisis', 'emergency', 'intense', 'stakes', 'clash', 'conflict']
    chill_words = ['quiet', 'porch', 'coffee', 'tea', 'relax', 'rain', 'cozy', 'stroll', 'afternoon', 'weekend', 'peaceful', 'calm', 'breeze']
    uplifting_words = ['hope', 'inspire', 'overcome', 'breakthrough', 'forward', 'rise', 'light', 'stronger', 'believe', 'healed']

    for w in sad_words:
        if w in c_lower: scores['melancholic'] += 25
    for w in happy_words:
        if w in c_lower: scores['energetic'] += 25
    for w in romantic_words:
        if w in c_lower: scores['romantic'] += 25
    for w in dramatic_words:
        if w in c_lower: scores['dramatic'] += 25
    for w in chill_words:
        if w in c_lower: scores['chill'] += 20
    for w in uplifting_words:
        if w in c_lower: scores['uplifting'] += 20

    top_tone, top_score = max(scores.items(), key=lambda x: x[1])
    if top_score >= 18:
        return top_tone
    return 'balanced'


TEMPO_POOLS_BY_TONE = {
    'melancholic': ['slow-burn 74 bpm', 'intimate 80 bpm', 'gentle 86 bpm', 'steady 90 bpm'],
    'energetic': ['driving 116 bpm', 'upbeat 120 bpm', 'bouncy 124 bpm', 'high-energy 128 bpm'],
    'romantic': ['tender 82 bpm', 'smooth 88 bpm', 'warm 94 bpm', 'gentle 100 bpm'],
    'chill': ['laid-back 80 bpm', 'relaxed 86 bpm', 'mellow 92 bpm', 'chill 96 bpm'],
    'dramatic': ['dark 78 bpm', 'building 86 bpm', 'driving 96 bpm', 'tense 106 bpm'],
    'uplifting': ['steady 104 bpm', 'driving 110 bpm', 'inspiring 114 bpm', 'anthem 118 bpm'],
    'balanced': ['steady 104 bpm', 'driving 112 bpm', 'upbeat 118 bpm', 'smooth 96 bpm'],
}

VOCAL_STYLES_BY_TONE = {
    'male': {
        'melancholic': ['intimate soulful male vocals', 'tender emotional male vocals', 'warm expressive male lead'],
        'energetic': ['bright articulate male voice', 'clear upfront male vocals', 'punchy expressive male lead'],
        'romantic': ['smooth resonant male lead', 'intimate soulful male vocals', 'warm expressive male lead'],
        'chill': ['laid-back male vocals', 'smooth resonant male lead', 'intimate soulful male vocals'],
        'dramatic': ['deep resonant male lead', 'crisp articulate male voice', 'expressive emotive male vocals'],
        'uplifting': ['warm expressive male lead', 'clear upfront male vocals', 'soaring emotive male vocals'],
        'balanced': ['clear upfront male vocals', 'warm expressive male lead', 'smooth resonant male lead'],
    },
    'female': {
        'melancholic': ['intimate soulful female lead', 'tender emotional female voice', 'warm expressive female lead'],
        'energetic': ['bright articulate female voice', 'clear upfront female vocals', 'energetic expressive female lead'],
        'romantic': ['intimate soulful female lead', 'crisp airy female vocals', 'warm expressive female lead'],
        'chill': ['crisp airy female vocals', 'mellow soulful female lead', 'relaxed female vocals'],
        'dramatic': ['expressive emotive female vocals', 'crisp articulate female voice', 'resonant female lead'],
        'uplifting': ['warm expressive female lead', 'clear upfront female vocals', 'soaring articulate female voice'],
        'balanced': ['clear upfront female vocals', 'warm expressive female lead', 'crisp articulate female voice'],
    },
    'duet': {
        'melancholic': ['tender male-female harmonies', 'intimate conversational duet'],
        'energetic': ['clear male-female duet vocals', 'dynamic dual lead, clear lyrics'],
        'romantic': ['intertwined male-female vocals', 'warm intimate duet harmonies'],
        'chill': ['relaxed acoustic duet', 'conversational dual lead vocals'],
        'dramatic': ['dramatic dual lead vocals', 'conversational high-stakes duet'],
        'uplifting': ['harmonious uplifting duet', 'dynamic dual lead, clear lyrics'],
        'balanced': ['clear male-female duet vocals', 'conversational dual lead vocals'],
    },
    'instrumental': {
        'melancholic': ['instrumental, emotive lead melody', 'instrumental, gentle acoustic lead'],
        'energetic': ['instrumental, driving melodic top line', 'instrumental, punchy synth lead'],
        'romantic': ['instrumental, tender acoustic lead', 'instrumental, warm melodic top line'],
        'chill': ['instrumental, mellow melodic top line', 'instrumental, relaxed lead'],
        'dramatic': ['instrumental, dramatic cinematic lead', 'instrumental, intense melodic lead'],
        'uplifting': ['instrumental, inspiring lead melody', 'instrumental, soaring lead'],
        'balanced': ['instrumental, melodic top line', 'instrumental, acoustic lead'],
    }
}

VOCAL_DELIVERY_STYLES = {
    "male": ["clear upfront male vocals", "warm expressive male lead", "smooth resonant male lead"],
    "female": ["clear upfront female vocals", "warm expressive female lead", "bright articulate female voice"],
    "duet": ["clear male-female duet vocals", "conversational dual lead vocals"],
    "instrumental": ["instrumental, melodic top line", "instrumental, acoustic lead"],
}

MIX_POOLS_BY_TONE = {
    'melancholic': ['warm emotive mix', 'spacious intimate mix', 'clean acoustic mix'],
    'energetic': ['punchy radio mix', 'bright modern mix', 'tight stereo mix'],
    'romantic': ['silky smooth mix', 'warm soul mix', 'intimate room mix'],
    'chill': ['cozy tape mix', 'clean airy mix', 'spacious ambient mix'],
    'dramatic': ['dynamic cinematic mix', 'deep punchy mix', 'wide stereo mix'],
    'uplifting': ['bright polished mix', 'spacious modern mix', 'clean radio mix'],
    'balanced': ['clean radio mix', 'punchy stereo mix', 'bright polished mix'],
}

SUNO_GENRE_TONE_PALETTES = {
    "Pop": {
        "melancholic": {
            "substyles": ["Acoustic pop ballad", "Emotive piano pop", "Melancholic pop"],
            "instruments": ["felt piano, subtle strings, soft acoustic", "Rhodes keys, acoustic guitar, soft brushes", "delicate piano chords, subtle sub-bass, snaps"],
        },
        "energetic": {
            "substyles": ["Dance-pop", "Upbeat radio pop", "Bright electro-pop"],
            "instruments": ["acoustic guitar, bright synths, snaps", "deep synth bass, muted guitar, claps", "grand piano, punchy drums, synth lead"],
        },
        "romantic": {
            "substyles": ["Sweet acoustic pop", "Romantic pop ballad", "Warm melodic pop"],
            "instruments": ["warm acoustic guitar, soft piano, light snaps", "Rhodes keys, clean guitar, tight drums", "fingerstyle acoustic, soft pads, light percussion"],
        },
        "chill": {
            "substyles": ["Chill bedroom pop", "Breezy indie pop", "Mellow acoustic pop"],
            "instruments": ["fingerstyle acoustic, arps, deep sub", "warm electric piano, clean guitar, snaps", "mellow Rhodes, subtle beat, soft synth"],
        },
        "dramatic": {
            "substyles": ["Dramatic cinematic pop", "Dark electro-pop", "Moody pop"],
            "instruments": ["grand piano, heavy sub-bass, punchy drums", "soaring lead synth, driving bass, crisp snares", "dark synth pads, muted guitar, dramatic kick"],
        },
        "uplifting": {
            "substyles": ["Uplifting radio pop", "Anthem pop hook", "Driving acoustic pop"],
            "instruments": ["grand piano, punchy drums, synth lead", "acoustic guitar, bright synths, snaps", "building piano, soaring guitar, dynamic drums"],
        },
        "balanced": {
            "substyles": ["Radio pop", "Acoustic pop", "Dance-pop", "Melodic pop"],
            "instruments": ["acoustic guitar, bright synths, snaps", "Rhodes keys, clean guitar, tight drums", "deep synth bass, muted guitar, claps"],
        },
    },
    "K-Pop Style (Clear English Vocals)": {
        "melancholic": {
            "substyles": ["K-Pop piano ballad", "Emotive K-Pop acoustic", "Heartfelt K-Pop"],
            "instruments": ["emotive grand piano, subtle strings, soft percussion", "delicate synth plucks, acoustic guitar, sub-bass", "warm Rhodes chords, emotional strings, brush drums"],
        },
        "energetic": {
            "substyles": ["K-Pop dance", "High-energy K-Pop", "K-Pop electro groove"],
            "instruments": ["punchy 808 bass, crisp percussion, plucks", "trap-pop drums, brass synth hits, riffs", "groovy bass, four-on-the-floor kick, synths"],
        },
        "romantic": {
            "substyles": ["Slick K-Pop R&B", "Romantic K-Pop groove", "Sweet K-Pop ballad"],
            "instruments": ["slick R&B synth chords, electronic drums", "warm Rhodes piano, smooth 808s, guitar fills", "delicate synth bells, fingerstyle guitar, light beat"],
        },
        "chill": {
            "substyles": ["Chill K-Pop groove", "Laid-back K-Pop R&B", "Sunset K-Pop"],
            "instruments": ["mellow synth pads, soft 808 kick, clean guitar", "warm electric piano, rimshot groove, sub-bass"],
        },
        "dramatic": {
            "substyles": ["Dramatic K-Pop", "Dark concept K-Pop", "Intense K-Pop drop"],
            "instruments": ["dark brass hits, distorted 808 bass, trap drums", "cinematic strings, punchy synths, intense beat"],
        },
        "uplifting": {
            "substyles": ["Uplifting K-Pop anthem", "Bright K-Pop dance", "Inspiring K-Pop"],
            "instruments": ["bright synth brass, driving pop beat, soaring guitar", "punchy 808, uplifting piano chords, claps"],
        },
        "balanced": {
            "substyles": ["K-Pop dance", "K-Pop electro groove", "Slick K-Pop R&B"],
            "instruments": ["punchy 808 bass, crisp percussion, plucks", "trap-pop drums, brass synth hits, riffs"],
        },
    },
    "Synth-Pop / 80s Retro": {
        "melancholic": {
            "substyles": ["Nostalgic synth ballad", "80s slow-burn ballad", "Wistful new wave"],
            "instruments": ["Roland Juno pads, chorus guitar, soft LinnDrum", "gated reverb snare, mournful lead synth, analog bass", "ambient Oberheim chords, emotive bassline, snaps"],
        },
        "energetic": {
            "substyles": ["Neon electro-pop", "Retro synthwave", "80s dance-pop"],
            "instruments": ["arpeggiated bass, brass synths, LinnDrum beat", "Juno synth chords, chorus guitar, e-drums", "pulsing analog synth bass, gated snare, bright leads"],
        },
        "romantic": {
            "substyles": ["80s romantic synth", "Vintage love wave", "Neon slow-jam"],
            "instruments": ["shimmering analog pads, clean chorus guitar, LinnDrum", "warm Juno chords, smooth synth bass, soft rimshot"],
        },
        "chill": {
            "substyles": ["Chillwave retro", "Downtempo synthwave", "Night drive retro"],
            "instruments": ["mellow tape synths, dreamy chorus guitar, soft beat", "analog pads, relaxed synth bass, subtle snare"],
        },
        "dramatic": {
            "substyles": ["Darkwave synth-pop", "Intense 80s thriller", "Cyberpunk retro"],
            "instruments": ["rolling bassline, soaring lead synth, hi-hats", "distorted analog bass, dark Oberheim stabs, gated drums"],
        },
        "uplifting": {
            "substyles": ["Uplifting synthwave", "Neon anthem pop", "Triumphant new wave"],
            "instruments": ["soaring synth leads, driving LinnDrum, bright brass", "arpeggiated bass, triumphant Juno chords, claps"],
        },
        "balanced": {
            "substyles": ["80s synth-pop", "Retro synthwave", "Neon electro-pop"],
            "instruments": ["analog synth bass, Oberheim pads, gated snare", "Juno synth chords, chorus guitar, e-drums"],
        },
    },
    "Indie Pop": {
        "melancholic": {
            "substyles": ["Melancholic indie pop", "Sad indie ballad", "Wistful chamber pop"],
            "instruments": ["upright piano, warm acoustic guitar, brush snare", "muted Telecaster, delicate cello, room reverb", "fingerstyle acoustic, melancholic bass, soft drums"],
        },
        "energetic": {
            "substyles": ["Upbeat indie groove", "Jangle indie pop", "Indie garage-pop"],
            "instruments": ["jangly electric guitar, melodic bass, drums", "fuzzy bass, clean Telecaster riffs, tambourine", "bouncy rhythm guitar, driving bassline, handclaps"],
        },
        "romantic": {
            "substyles": ["Dreamy indie pop", "Sweet indie romance", "Bedroom indie love"],
            "instruments": ["sparkling guitars, Juno synth pads, tight drums", "fingerstyle acoustic, subtle glockenspiel, soft bass"],
        },
        "chill": {
            "substyles": ["Breezy indie pop", "Lo-fi bedroom indie", "Mellow indie folk"],
            "instruments": ["clean chorus guitar, lazy drum machine, warm bass", "muted upright piano, warm rhythm guitar, organic drums"],
        },
        "dramatic": {
            "substyles": ["Dramatic indie rock", "Moody indie pop", "Cinematic indie"],
            "instruments": ["distorted guitar swells, heavy room drums, driving bass", "haunting piano, gritty Telecaster riffs, building drums"],
        },
        "uplifting": {
            "substyles": ["Uplifting indie anthem", "Sunny indie pop", "Bright jangle pop"],
            "instruments": ["jangly 12-string guitar, melodic bass, driving drums", "bright acoustic strumming, tambourine, soaring hooks"],
        },
        "balanced": {
            "substyles": ["Jangle indie pop", "Dreamy indie pop", "Chamber indie pop"],
            "instruments": ["jangly electric guitar, melodic bass, drums", "fingerstyle acoustic, Juno pads, tight drums"],
        },
    },
    "Acoustic / Folk": {
        "melancholic": {
            "substyles": ["Heartbroken folk ballad", "Poignant acoustic ballad", "Wistful indie folk"],
            "instruments": ["fingerpicked guitar, weeping cello, soft shaker", "wooden acoustic, delicate violin, upright piano", "open-tuned acoustic, subtle double bass, brush snare"],
        },
        "energetic": {
            "substyles": ["Upbeat bluegrass folk", "Stomp-and-clap folk", "Rootsy acoustic stomp"],
            "instruments": ["strummed dreadnought, rustic banjo, double bass", "fast fingerpicking, lively fiddle, foot stomp rhythm", "two acoustic guitars, driving mandolin, kick drum"],
        },
        "romantic": {
            "substyles": ["Tender acoustic folk", "Sweet porch folk", "Romantic acoustic ballad"],
            "instruments": ["dual acoustic guitars, slide dobro, gentle bass", "warm fingerpicked guitar, soft cello, gentle shaker"],
        },
        "chill": {
            "substyles": ["Mellow campfire folk", "Peaceful acoustic", "Breezy front-porch folk"],
            "instruments": ["warm acoustic strum, subtle harmonica, gentle bass", "fingerpicked guitar, upright piano, quiet brushes"],
        },
        "dramatic": {
            "substyles": ["Dark Appalachian folk", "Dramatic murder ballad", "Brooding roots"],
            "instruments": ["mournful fiddle, minor acoustic picking, deep kick", "haunting banjo, bowed double bass, dramatic stomp"],
        },
        "uplifting": {
            "substyles": ["Uplifting Americana folk", "Inspiring acoustic anthem", "Triumphant roots"],
            "instruments": ["building acoustic strumming, soaring violin, double bass", "12-string guitar, rustic banjo, foot stomps, choir"],
        },
        "balanced": {
            "substyles": ["Acoustic folk", "Contemporary folk", "Indie folk ballad"],
            "instruments": ["fingerpicked guitar, subtle cello, soft shaker", "strummed dreadnought, rustic banjo, double bass"],
        },
    },
    "R&B / Contemporary Soul": {
        "melancholic": {
            "substyles": ["Heartbreak R&B ballad", "Slow-burn soul ballad", "Poignant neo-soul"],
            "instruments": ["mellow grand piano, fingerstyle bass, 808s", "Rhodes piano, silky sub-bass, weeping guitar fills", "vintage Wurlitzer, slow rimshot, deep bassline"],
        },
        "energetic": {
            "substyles": ["Upbeat modern R&B", "Funky soulful groove", "R&B dance-pop"],
            "instruments": ["syncopated bass, crisp snaps, brass synth stabs", "Stratocaster chords, bouncy 808s, talkbox accents", "Rhodes keys, punchy electronic drums, vocal chops"],
        },
        "romantic": {
            "substyles": ["Smooth neo-soul", "Romantic slow-jam", "Velvet soul groove"],
            "instruments": ["Rhodes piano, silky sub-bass, rimshot groove", "Stratocaster chords, Hammond organ, deep bass", "warm Wurlitzer, expressive guitar licks, snaps"],
        },
        "chill": {
            "substyles": ["Chill neo-soul groove", "Late-night bedroom R&B", "Lo-fi soul"],
            "instruments": ["warm Rhodes chords, lazy rimshot, sub-bass", "clean electric guitar, soft finger snaps, mellow keys"],
        },
        "dramatic": {
            "substyles": ["Dramatic soul ballad", "Intense cinematic R&B", "Dark soul groove"],
            "instruments": ["heavy sub-bass, emotive grand piano, building 808s", "swelling Hammond organ, soaring guitar lead, deep drums"],
        },
        "uplifting": {
            "substyles": ["Uplifting soul anthem", "Gospel-infused R&B", "Inspiring modern soul"],
            "instruments": ["Hammond B3 organ swells, uplifting piano, driving beat", "soaring guitar chords, punchy bass, gospel claps"],
        },
        "balanced": {
            "substyles": ["Contemporary R&B", "Neo-soul groove", "Smooth soul ballad"],
            "instruments": ["Rhodes piano, silky sub-bass, rimshot groove", "Wurlitzer chords, guitar licks, neo-soul snare"],
        },
    },
    "Country / Americana": {
        "melancholic": {
            "substyles": ["Heartbreak country ballad", "Wistful acoustic country", "Sad highway ballad"],
            "instruments": ["weeping pedal steel, acoustic guitar strum, brush snare", "fingerpicked acoustic, weeping fiddle, warm bass", "resonator guitar, honky-tonk piano, slow train beat"],
        },
        "energetic": {
            "substyles": ["Country road-trip rock", "Upbeat modern country", "Two-step country"],
            "instruments": ["12-string guitar, driving electric guitar, kick drum", "telecaster twang, driving bass, crisp snare drum", "acoustic strum, pedal steel, energetic drums"],
        },
        "romantic": {
            "substyles": ["Sweet country love song", "Warm porch Americana", "Tender country duet"],
            "instruments": ["fingerpicked acoustic, gentle pedal steel, soft bass", "acoustic guitar strum, warm fiddle, subtle brushes"],
        },
        "chill": {
            "substyles": ["Mellow backroads country", "Relaxed Americana", "Campfire country"],
            "instruments": ["acoustic guitar strum, subtle harmonica, lazy snare", "resonator guitar, upright bass, gentle shaker"],
        },
        "dramatic": {
            "substyles": ["Dark outlaw country", "Dramatic Southern gothic", "High-stakes country"],
            "instruments": ["gritty Telecaster riffs, ominous pedal steel, heavy kick", "haunting resonator guitar, deep bass, dramatic drums"],
        },
        "uplifting": {
            "substyles": ["Uplifting country anthem", "Heartland rock anthem", "Inspiring Americana"],
            "instruments": ["soaring electric guitar, acoustic strum, driving drums", "pedal steel swells, big chorus piano, energetic kick"],
        },
        "balanced": {
            "substyles": ["Modern country", "Americana roots", "Country road-trip"],
            "instruments": ["acoustic guitar strum, pedal steel, train-beat snare", "resonator guitar, honky-tonk piano, walking bass"],
        },
    },
    "Funk / Disco Groove": {
        "melancholic": {
            "substyles": ["Slow-burn retro soul", "Melancholic funk ballad", "Bittersweet groove"],
            "instruments": ["weeping wah guitar, Rhodes piano, slow bass groove", "mellow Clavinet, subtle horn swells, brush drums", "expressive bassline, gentle electric piano, soft rimshot"],
        },
        "energetic": {
            "substyles": ["Disco funk", "Modern funk groove", "Nu-disco pulse"],
            "instruments": ["slap bass, guitar chops, brass stabs, four-on-floor", "syncopated bass, Clavinet wah, tight horn stabs", "pulsing synth bass, Nile Rodgers rhythm, congas"],
        },
        "romantic": {
            "substyles": ["Smooth funk slow-jam", "Sensual disco soul", "Velvet groove"],
            "instruments": ["warm Rhodes chords, smooth bassline, clean guitar licks", "soft Clavinet, gentle brass swells, disco strings"],
        },
        "chill": {
            "substyles": ["Laid-back low-end funk", "Chillout groove", "Coffeehouse funk"],
            "instruments": ["groovy bassline, electric piano, live drums", "subtle guitar wah, warm electric piano, relaxed kick"],
        },
        "dramatic": {
            "substyles": ["Dramatic cinematic funk", "Dark 70s groove", "Action funk chase"],
            "instruments": ["aggressive slap bass, horn stabs, driving wah guitar", "tense Clavinet riff, distorted bass, heavy breakbeat"],
        },
        "uplifting": {
            "substyles": ["Celebration disco", "Triumphant funk groove", "Joyful dance funk"],
            "instruments": ["bright brass section, Nile Rodgers guitar, driving slap bass", "soaring disco strings, funky bassline, handclaps"],
        },
        "balanced": {
            "substyles": ["Disco funk", "Modern funk groove", "70s style groove"],
            "instruments": ["slap bass, guitar chops, brass stabs, four-on-floor", "syncopated bass, Clavinet wah, tight horn stabs"],
        },
    },
    "Reggae / Tropical Pop": {
        "melancholic": {
            "substyles": ["Poignant roots reggae", "Melancholic island ballad", "Wistful dub reggae"],
            "instruments": ["minor guitar skank, deep dub bass, weeping organ, one-drop", "slow acoustic island strum, mellow marimba, dub delay"],
        },
        "energetic": {
            "substyles": ["Tropical pop dance", "Upbeat island groove", "Sunny festival reggae"],
            "instruments": ["island guitar skank, dub bass, organ bubble, drums", "marimba accents, warm bass, steel pan, percussion", "offbeat guitar, roots bassline, brass horn stabs"],
        },
        "romantic": {
            "substyles": ["Lovers rock reggae", "Sweet tropical romance", "Island slow-dance"],
            "instruments": ["clean offbeat guitar, warm sub-bass, soft horns, one-drop", "acoustic strum, tropical steel pan, gentle percussion"],
        },
        "chill": {
            "substyles": ["Breezy summer reggae", "Chill island acoustic", "Relaxed beach reggae"],
            "instruments": ["acoustic strum, tropical percussion, warm sub-bass", "mellow organ bubble, light guitar skank, relaxed drums"],
        },
        "dramatic": {
            "substyles": ["Heavy dub reggae", "Dramatic roots rebel", "Steppers reggae"],
            "instruments": ["heavy dub bass, echoing rimshot, dark horn stabs", "minor skank guitar, deep bass drops, tape echo"],
        },
        "uplifting": {
            "substyles": ["Uplifting island pop", "Joyful roots reggae", "Sunny tropical anthem"],
            "instruments": ["bright steel pan, lively guitar skank, cheerful horns", "driving reggae beat, warm bass, bright marimba"],
        },
        "balanced": {
            "substyles": ["Tropical pop", "Roots reggae pop", "Island groove"],
            "instruments": ["island guitar skank, dub bass, organ bubble, drums", "marimba accents, warm bass, steel pan, percussion"],
        },
    },
    "Jazz / Bossa Nova": {
        "melancholic": {
            "substyles": ["Late-night blue note jazz", "Melancholic bossa ballad", "Smoky jazz ballad"],
            "instruments": ["muted trumpet, delicate piano voicings, brushed snare", "nylon guitar, gentle upright bass, soft brush clicks", "hollowbody guitar, emotive grand piano, walking bass"],
        },
        "energetic": {
            "substyles": ["Swinging jazz groove", "Fast bossa nova", "Upbeat samba jazz"],
            "instruments": ["walking upright bass, lively piano swing, snappy ride cymbal", "bright nylon guitar, cuica rhythm, energetic bossa beat"],
        },
        "romantic": {
            "substyles": ["Bossa nova romance", "Sensual cafe jazz", "Sweet bossa groove"],
            "instruments": ["nylon guitar, gentle upright bass, brushed snare", "delicate piano voicings, acoustic bass, rim clicks", "hollowbody guitar, soft grand piano, walking bass"],
        },
        "chill": {
            "substyles": ["Acoustic bossa lounge", "Smoky jazz lounge", "Relaxed afternoon jazz"],
            "instruments": ["acoustic guitar, gentle flute lead, fingerstyle bass", "mellow Rhodes chords, soft upright bass, quiet brush"],
        },
        "dramatic": {
            "substyles": ["Noir jazz ballad", "Dramatic modal jazz", "Cinematic jazz noir"],
            "instruments": ["brooding double bass, dissonant piano chords, dark trumpet", "tense ride cymbal, bowed double bass, moody guitar"],
        },
        "uplifting": {
            "substyles": ["Joyful bossa nova", "Bright swing jazz", "Breezy coastal samba"],
            "instruments": ["sun-drenched nylon guitar, smiling piano chords, cheerful drums", "lively flute lead, swinging bassline, crisp percussion"],
        },
        "balanced": {
            "substyles": ["Bossa nova", "Smooth jazz vocal", "Acoustic bossa"],
            "instruments": ["nylon guitar, gentle upright bass, brushed snare", "hollowbody guitar, soft grand piano, walking bass"],
        },
    },
    "Cinematic / Ballad": {
        "melancholic": {
            "substyles": ["Heartbroken piano ballad", "Tearful cinematic ballad", "Poignant string ballad"],
            "instruments": ["felt piano, weeping string quartet, delicate cello", "intimate grand piano, mournful strings, ambient reverb", "delicate acoustic piano, subtle French horns, soft harp"],
        },
        "energetic": {
            "substyles": ["Epic cinematic pop", "Action orchestral pop", "Heroic cinematic theme"],
            "instruments": ["huge tympani drums, soaring French horns, driving strings", "dynamic orchestral percussion, power piano, big brass"],
        },
        "romantic": {
            "substyles": ["Romantic cinematic ballad", "Grand wedding ballad", "Tender movie theme"],
            "instruments": ["grand piano, symphonic strings, dynamic crescendo", "warm cinematic cello, ambient piano, building percussion"],
        },
        "chill": {
            "substyles": ["Intimate ambient ballad", "Quiet movie reflection", "Peaceful chamber ballad"],
            "instruments": ["soft felt piano, gentle ambient pads, quiet cello", "delicate piano ripples, subtle strings, warm soundstage"],
        },
        "dramatic": {
            "substyles": ["High-stakes cinematic drama", "Dark cinematic ballad", "Tense orchestral score"],
            "instruments": ["delicate piano, French horns, cinematic sub-bass", "heavy brass stabs, pounding tympani, dramatic string swells"],
        },
        "uplifting": {
            "substyles": ["Grand triumphant ballad", "Inspirational movie anthem", "Epic rising ballad"],
            "instruments": ["building piano, soaring violin crescendo, huge tympani", "grand piano, full symphonic strings, triumphant climax"],
        },
        "balanced": {
            "substyles": ["Cinematic ballad", "Grand orchestral ballad", "Emotive piano ballad"],
            "instruments": ["grand piano, symphonic strings, dynamic crescendo", "cinematic cello, ambient piano, building percussion"],
        },
    },
    "Lo-Fi / Chillhop": {
        "melancholic": {
            "substyles": ["Rainy day lofi", "Sad boy chillhop", "Heartbroken tape beats"],
            "instruments": ["detuned tape piano, muted guitar loops, vinyl rain", "Rhodes chords, vinyl crackle, sad trumpet sample, beat", "melancholic tape keys, upright bass, dusty boom-bap"],
        },
        "energetic": {
            "substyles": ["Upbeat boom-bap lofi", "Groovy study beats", "Head-nod chillhop"],
            "instruments": ["punchy boom-bap drums, jazzy guitar chops, bouncy bass", "bright Rhodes chords, energetic vinyl beat, trumpet hits"],
        },
        "romantic": {
            "substyles": ["Sweet coffeehouse lofi", "Cozy romance chillhop", "Warm bedroom beats"],
            "instruments": ["music box chords, acoustic guitar loops, tape vibe", "warm Rhodes piano, gentle rimshot, vinyl crackle"],
        },
        "chill": {
            "substyles": ["Chill study beats", "Lo-fi chillhop", "Tape chillhop"],
            "instruments": ["Rhodes chords, vinyl crackle, upright bass, drums", "electric piano, muted trumpet, vinyl hiss, chill beat"],
        },
        "dramatic": {
            "substyles": ["Dark lofi beats", "Midnight noir chillhop", "Moody boom-bap"],
            "instruments": ["minor key tape piano, heavy sub-bass, vinyl hiss", "moody cello sample, dusty boom-bap drums, dark pads"],
        },
        "uplifting": {
            "substyles": ["Sunny morning lofi", "Hopeful chillhop", "Bright tape beats"],
            "instruments": ["bright acoustic guitar samples, uplifting Rhodes, snappy drums", "cheerful music box, warm bass, vinyl crackle"],
        },
        "balanced": {
            "substyles": ["Lo-fi chillhop", "Dusty boom-bap lofi", "Chill study beats"],
            "instruments": ["Rhodes chords, vinyl crackle, upright bass, drums", "detuned tape piano, muted guitar loops, sub-bass"],
        },
    },
    "Melodic Chill Electronic": {
        "melancholic": {
            "substyles": ["Melancholic electronic", "Downtempo ambient sorrow", "Wistful chill electronica"],
            "instruments": ["felt piano melodies, ambient pads, slow sub-bass", "acoustic guitar textures, rolling bass, ambient reverb", "delicate synth plucks, soft vocal chops, deep bass"],
        },
        "energetic": {
            "substyles": ["Sunset melodic house", "Melodic electro-pop", "Upbeat chill dance"],
            "instruments": ["driving 4/4 chill pulse, bright piano, modular arps", "vocal chops, analog chords, percussion, sunset pulse"],
        },
        "romantic": {
            "substyles": ["Sensual downtempo", "Romantic chill electronic", "Warm ambient love"],
            "instruments": ["warm ambient synth pads, delicate piano, sub-bass, beat", "soft Rhodes, lush pads, gentle electronic pulse"],
        },
        "chill": {
            "substyles": ["Melodic chill electronic", "Downtempo chill", "Dream electronic"],
            "instruments": ["ambient synth pads, delicate piano, sub-bass, beat", "felt piano melodies, modular arps, gentle 4/4 pulse"],
        },
        "dramatic": {
            "substyles": ["Cinematic dark electronica", "Tense downtempo", "Moody ambient synth"],
            "instruments": ["pulsing modular synth, dark sub-bass, tense percussion", "heavy analog chords, distorted pads, dramatic drums"],
        },
        "uplifting": {
            "substyles": ["Uplifting melodic house", "Euphoric chill electronic", "Sunrise ambient pop"],
            "instruments": ["euphoric synth leads, bright piano, driving warm beat", "building arpeggios, soaring vocal pads, punchy kick"],
        },
        "balanced": {
            "substyles": ["Melodic chill electronic", "Ambient electro-pop", "Downtempo chill"],
            "instruments": ["ambient synth pads, delicate piano, sub-bass, beat", "vocal chops, analog chords, percussion, sunset pulse"],
        },
    },
}

# Legacy alias for backward compatibility
SUNO_GENRE_PALETTES = {
    genre: {
        "substyles": data["balanced"]["substyles"],
        "tempos": TEMPO_POOLS_BY_TONE["balanced"],
        "instruments": data["balanced"]["instruments"],
        "mixes": MIX_POOLS_BY_TONE["balanced"],
    }
    for genre, data in SUNO_GENRE_TONE_PALETTES.items()
}


def assemble_suno_prompt(substyle: str, tempo: str, voc: str, instruments: str, mix: str, max_len: int = 120) -> str:
    """Intelligently assembles and trims a Suno prompt to guarantee it stays strictly <= max_len."""
    full = f"{substyle}, {tempo}, {voc}, {instruments}, {mix}"
    if len(full) <= max_len:
        return full

    no_mix = f"{substyle}, {tempo}, {voc}, {instruments}"
    if len(no_mix) <= max_len:
        return no_mix

    items = [x.strip() for x in no_mix.split(",") if x.strip()]
    while len(", ".join(items)) > max_len and len(items) > 3:
        items.pop()
    trimmed = ", ".join(items)
    if len(trimmed) <= max_len:
        return trimmed

    return trimmed[:max_len - 3].rstrip() + "..."


def build_suno_style_prompt(
    genre: str,
    vocalist: str = "Male",
    mood_analysis: Optional[Dict[str, Any]] = None,
    creative_concept: str = "",
    max_length: int = 120
) -> str:
    """
    Builds an emotionally harmonized, keyword-rich Suno AI style prompt.
    Detects the emotional tone (sad, energetic, romantic, dramatic, chill, uplifting)
    from mood percentages and story concept, ensuring tempo (BPM), instruments,
    substyle, and vocal character match the song's true heart, while strictly
    guaranteeing length <= max_length (default 120 chars).
    """
    tone = detect_emotional_tone(mood_analysis, creative_concept)
    genre_data = SUNO_GENRE_TONE_PALETTES.get(genre, {})

    tone_pool = genre_data.get(tone) or genre_data.get("balanced") or list(genre_data.values())[0] if genre_data else None
    if not tone_pool:
        substyle = genre
        tempo = random.choice(TEMPO_POOLS_BY_TONE.get(tone, TEMPO_POOLS_BY_TONE["balanced"]))
        instruments = "melodic acoustic guitar, warm electric piano"
    else:
        substyle = random.choice(tone_pool["substyles"])
        tempo = random.choice(TEMPO_POOLS_BY_TONE.get(tone, TEMPO_POOLS_BY_TONE["balanced"]))
        instruments = random.choice(tone_pool["instruments"])

    voc_key = vocalist.lower().strip()
    if "female" in voc_key:
        voc_group = VOCAL_STYLES_BY_TONE["female"]
    elif "duet" in voc_key:
        voc_group = VOCAL_STYLES_BY_TONE["duet"]
    elif "instrumental" in voc_key:
        voc_group = VOCAL_STYLES_BY_TONE["instrumental"]
    else:
        voc_group = VOCAL_STYLES_BY_TONE["male"]

    voc_options = voc_group.get(tone, voc_group["balanced"])
    voc_delivery = random.choice(voc_options)
    mix = random.choice(MIX_POOLS_BY_TONE.get(tone, MIX_POOLS_BY_TONE["balanced"]))

    return assemble_suno_prompt(substyle, tempo, voc_delivery, instruments, mix, max_len=max_length)


def _norm(name: str) -> str:
    return name.lower().replace(" ", "").replace("-", "")

def parse_song_structure(structure_str: str) -> str:
    """Parses a structure string like 'Verse - Chorus - Bridge' into output format blocks."""
    s = structure_str.lower()
    if "through-composed" in s or "through composed" in s:
        return "[Verse 1]\n(4-6 lines)\n[Verse 2]\n(4-6 lines)\n[Verse 3]\n(4-6 lines)\n[Verse 4]\n(4-6 lines)"
    if "aaba" in s:
        return "[Verse 1]\n(4-6 lines)\n[Verse 2]\n(same number of lines as Verse 1)\n[Bridge]\n(4-8 lines)\n[Verse 3]\n(same number of lines as Verse 1)"

    # Split on " - ", dashes or arrows, but NOT on the hyphen inside "Pre-Chorus"
    parts = [p.strip() for p in re.split(r"\s+[-–—]\s+|\s*(?:→|->)\s*", structure_str) if p.strip()]

    def is_real_chorus(name: str) -> bool:
        n = _norm(name)
        return "chorus" in n and not n.startswith("pre")

    lines = []
    verse_count = pre_count = chorus_count = 0

    for idx, part in enumerate(parts):
        n = _norm(part)
        if n.startswith("verse"):
            verse_count += 1
            note = "(4-6 lines)" if verse_count == 1 else "(same number of lines as Verse 1)"
            lines.append(f"[Verse {verse_count}]\n{note}")
        elif n.startswith("prechorus"):
            pre_count += 1
            note = "(4 lines)" if pre_count == 1 else "(same as the first Pre-Chorus)"
            lines.append(f"[Pre-Chorus]\n{note}")
        elif "chorus" in n:
            chorus_count += 1
            is_last = not any(is_real_chorus(p) for p in parts[idx + 1:])
            if chorus_count == 1:
                lines.append("[Chorus]\n(4 lines)")
            elif is_last:
                lines.append("[Final Chorus]\n(the Chorus with at most one changed line)")
            else:
                lines.append("[Chorus]\n(identical to the first Chorus)")
        elif "bridge" in n:
            lines.append("[Bridge]\n(4-8 lines)")
        elif "intro" in n:
            lines.append("[Intro]\n(2-4 lines)")
        elif "outro" in n:
            lines.append("[Outro]\n(2-4 lines)")
        else:
            lines.append(f"[{part}]\n(4 lines)")

    return "\n".join(lines)


ESL_GOAL_BLOCK = """THE GOAL: the learner should be able to memorize ANY single line and use it as-is in real life.
Every line must be:
- Natural: something native speakers really say. Nothing awkward, inverted or overly poetic.
- One consistent dialect. No mixing of American and British forms.
- Short and easy to memorize.
- Part of ONE story told in order, with no jumps outside the story or setting.
- Clean: no explicit profanity. Mild words (hell, damn, God) only inside ordinary everyday expressions.
- Using target words in their everyday meaning. Never force a word in."""


def critic_calibration(profile: Dict[str, Any]) -> str:
    """Shared rubric for critic-only and refinement-loop evaluations."""
    return """REGISTER AND FAIR SCORING:
- Natural English includes educated and moderately formal speech when appropriate to the speaker and situation. Everyday meaning does not mean street slang.
- Basic / Neutral vocabulary is valid in every category. Judge actual meaning and context, not category labels.
- Ordinary pronouns and references are valid when clear in a real situation; the standalone test does not require every line to retell the story.
- Normal chorus repetition is not an authenticity flaw. CHORUS STORY TIMING IMMUNITY: A chorus is a recurring musical hook/refrain, NOT a linear plot beat. NEVER penalize, flag, or deduct points from chorus lines for chronological story order, narrative timing, or mentioning tools/actions before or after verses (e.g. asking for tools in Chorus 1 before a breakdown or in Chorus 3 after a fix is standard musical songwriting, NEVER a chronological contradiction). Do NOT critique story order or chronological timing in the chorus.
- Support every deduction with a concrete defect.
- Do not give 90+ to a line you cannot defend. A real song rarely has every line above 90. If almost all your scores are 90+, re-check yourself.
- Do not apply multiple deductions for the same underlying defect.
- Score every sung lyric line, including repeated occurrences; omit section tags and blank lines.
- Authenticity measures only the quality of the lyric lines. Missing, unused, or dropped target words and coverage percentages must NEVER lower line scores or overall_score.
- overall_score is the rounded arithmetic mean of the line scores, with equal weight per lyric line. Coverage and dropped_words are separate information, never a penalty or bonus.
- Recommend dropping a target only for an actual contextual or usage problem, never merely for its register.
""" + profile.get("critic_guidance", "")


def build_critic_prompt(
    draft: str,
    target_words: Optional[List[str]] = None,
    theme: str = "Basic / Neutral",
    genre: str = "Cinematic / Ballad",
    concept: str = "",
    dialect: str = "American English",
    errors: Optional[List[str]] = None
) -> str:
    """
    Constructs the complete, strict ESL Critic Prompt for line-by-line authenticity evaluation.
    This prompt can be run via Gemini API or copied by the user to run externally in Claude 3.5 Sonnet / GPT-4o.
    """
    words_list = target_words or []
    words_str = ", ".join(words_list) if words_list else "None specified"
    p = get_category_profile(theme)
    concept_str = concept.strip() if concept else p.get("default_story", "")

    error_section = ""
    if errors:
        error_section = f"\nSYSTEM INSPECTOR FLAGS (Reference only):\n{json.dumps(errors, indent=2)}\n"

    return f"""You are a strict ESL lyric critic. You do NOT rewrite anything. Score each line from 0 to 100 against THE GOAL below.
Judge each line in the context of the whole song (so you can catch contradictions), but score only that line.

{ESL_GOAL_BLOCK}

CONTEXTUAL ANCHORS:
- Theme: "{theme}"
- Category guidance: Setting: {p.get('setting', '')}. Register: {p.get('register', '')}.
- Musical Genre: "{genre}"
- Core Story / Setting: "{concept_str}"
- Dialect: {dialect}
- Target words (the only words that count as target words): {words_str}

{critic_calibration(p)}

Start every line at 100 and subtract:
- Not something a native speaker would say in this setting (poetic, literary, inverted word order): -25
- Filler added for rhyme or rhythm, or vague when read alone ("I hope that you can see"): -20
- Fails the standalone test (not useful or not understandable on its own): -20
- Target word used in a forced, odd or non-everyday way (apply only to the target words above): -25
- Contradicts the story or the narrator's stance, or jumps outside the story/setting (evaluate verses and bridge for chronological story order; NEVER penalize chorus lines for chronological timing/order as chorus is a recurring hook): -25
- Stiff form where a contraction is natural in this setting ("I am sorry", "do not"): -10
- Mixes dialects in the line, or uses forms outside {dialect}: -15
- Longer than 9 syllables or hard to sing/memorize: -10
- Crude language beyond ordinary expressions: -20

Rules:
- If any deduction applies, the score cannot exceed 89. A line with no deductions scores 90-100.
- Apply the target-word deduction only to the official target words listed above.
- For each line return: number, the line, score, and a short issue (or "none").
- If a target word completely destroys the realism of the scene or sounds forced, list it in dropped_words.
{error_section}
SONG LYRICS TO EVALUATE:
{draft}

OUTPUT JSON SCHEMA:
{{
    "overall_score": 0-100,
    "dropped_words": ["word1"],
    "dropped_reasons": {{"word1": "reason"}},
    "lines_review": [
        {{
            "number": 1,
            "line": "exact line text",
            "score": 0-100,
            "issue": "short reason or 'none'"
        }}
    ]
}}
"""


def build_manual_surgical_prompt(
    lyrics_text: str,
    line_breakdown: List[Dict[str, Any]],
    theme: str = "Basic / Neutral",
    genre: str = "Cinematic / Ballad",
    concept: str = "",
    target_words: Optional[List[str]] = None,
    selected_domain: Optional[str] = None
) -> str:
    """
    Constructs a surgical prompt ready to copy-paste into Claude 3.5 Sonnet / GPT-4o,
    categorizing lines strictly by score: 🟢 >= 90 (Locked), 🟡 75-89 (Optional Polish), 🔴 < 75 (Rewrite Required).
    """
    domain_to_use = selected_domain if selected_domain else theme
    p = get_category_profile(domain_to_use)

    story_concept = concept.strip() if concept else p["default_story"]

    words_list = target_words or []
    words_joined = ", ".join(words_list) if words_list else "None specified"

    # Strict code-based thresholding
    passed_lines = [l for l in line_breakdown if l.get("score", 0) >= 90]
    critical_lines = [l for l in line_breakdown if l.get("score", 0) < 75]
    warning_lines = [l for l in line_breakdown if 75 <= l.get("score", 0) < 90]

    crit_text = "\n".join([f'- Line: "{l.get("line", "")}"\n  Score: {l.get("score", 0)}%\n  Critique: {l.get("comment") or l.get("issue", "")}' for l in critical_lines]) if critical_lines else "None (All lines passed critical checks!)"
    warn_text = "\n".join([f'- Line: "{l.get("line", "")}"\n  Score: {l.get("score", 0)}%\n  Critique: {l.get("comment") or l.get("issue", "")}' for l in warning_lines]) if warning_lines else "None"
    passed_text = "\n".join([f'- "{l.get("line", "")}"' for l in passed_lines]) if passed_lines else "None"

    # Map status by line text
    status_dict = {}
    for l in line_breakdown:
        raw_txt = l.get("line", "").strip().lower()
        score = l.get("score", 0)
        if score >= 90:
            eff = "✅"
        elif score >= 75:
            eff = "⚠️"
        else:
            eff = "❌"
        if raw_txt:
            status_dict[raw_txt] = eff

    annotated_lines = []
    for raw_l in lyrics_text.splitlines():
        cleaned = raw_l.strip().lower().strip(",").strip(".")
        if not raw_l.strip() or raw_l.strip().startswith("["):
            annotated_lines.append(raw_l)
        else:
            match_status = None
            for k, line_status in status_dict.items():
                if k in cleaned or cleaned in k:
                    match_status = line_status
                    break
            if match_status == "❌":
                annotated_lines.append(f"[🚨 REWRITE REQUIRED ❌] {raw_l}")
            elif match_status == "⚠️":
                annotated_lines.append(f"[⚠️ OPTIONAL POLISH] {raw_l}")
            elif match_status == "✅":
                annotated_lines.append(f"[🔒 LOCKED ✅ - DO NOT TOUCH] {raw_l}")
            else:
                annotated_lines.append(f"[⚠️ OPTIONAL POLISH] {raw_l}")
    annotated_lyrics_block = "\n".join(annotated_lines)

    domain_dir = p.get("domain_directive", "")
    domain_guidance_str = f" {domain_dir}" if domain_dir else ""

    return f"""You are an expert English linguist and a professional ESL teacher who edits song lyrics for learners.
Your mission is to perform SURGICAL REPAIRS on the song lyrics below.

{ESL_GOAL_BLOCK}

CRITICAL PEDAGOGICAL MISSION:
This song is an educational song built around a strict list of target vocabulary words.
Every target word that is currently in the lyrics MUST be preserved. Do not add target words that are missing. Dropping or replacing a present target word with a synonym is a critical failure.

CONTEXTUAL ANCHORS:
- Theme: "{domain_to_use}"
- Category guidance: Setting: {p['setting']}. Register: {p['register']}.{domain_guidance_str}
- Musical Genre: "{genre}"
- Core Story / Setting / Concept: "{story_concept}"
- Dialect: American English (never mix dialects; use one consistent variety of English)

🎯 TARGET VOCABULARY (Preserve every target word currently in the lyrics; do not add missing ones):
{words_joined}

🔒 VERIFIED GREEN LINES ({len(passed_lines)} Lines - 100% LOCKED, DO NOT CHANGE):
{passed_text}

🚨 CRITICAL FLAWED LINES (Must be rewritten - Score < 75%):
{crit_text}

⚠️ MINOR WARNING LINES (Only tweak if it improves flow - Score 75-89%):
{warn_text}

---
CURRENT ANNOTATED SONG LYRICS (Follow the tags next to each line):
{annotated_lyrics_block}
---

=== SURGICAL REPAIR INSTRUCTIONS (OVERRIDE ANY CONFLICT ABOVE) ===

A. GREEN LINES (🔒) ARE LOCKED IN THE LYRICS OUTPUT.
   Never delete, reorder, merge, split, or reword them in Part 1. Treat them as fixed anchors. Every green line must appear in the output exactly once per place it appears now, in the same position.

B. EDIT SCOPE: Edit ONLY the ⚠️ (yellow) and ❌ (red) lines. If none are red, do not invent problems. A yellow line may be kept unchanged if no real improvement exists.

C. TARGET WORDS & TONE:
   - Every target word currently in the lyrics must remain intact. Do not add target words that are missing.
   - Do NOT replace any present target word with a synonym.
   - Do NOT add new profanity or crude vulgarities in edited lines. Existing coarse language inside green lines is intentional (street-life realism) and must not be treated as an error.

D. RED LINES FOR EDITED LINES (OVERRIDE ALL GOALS BELOW):
   An edited line must never be awkward, stiff, inverted, poetic, outside the story, an abrupt jump, empty of learning value, or have an unclear speaker. If you cannot fix a line without crossing a red line, keep the original line and say so in the change log. This applies to yellow and red lines only; green lines stay locked.

E. IMPROVEMENT GOALS FOR EDITED LINES (priority order):
   1. THEMATIC CONSISTENCY & SETTING CONTINUITY: Every edited line must stay inside the song's theme ("{domain_to_use}") and established setting / story ("{story_concept}"). Do not introduce new locations, characters, or topics that drift away from the central story. If a line does not serve the core story, rewrite it.
   2. PRACTICAL USABILITY:
      - An ESL learner who memorizes the line should be able to say it naturally in this setting. Prefer natural spoken English over poetic or literary phrasing.
      - Use natural contractions (I'm, don't, can't); avoid stiff forms unless the setting requires formality.
      - Standalone test: read alone, the line must be natural and useful.
   3. NO FORCED RHYME: A line must add real narrative meaning, not exist only to rhyme.
   4. NO REPETITION: Avoid repeating the same opening word or key noun in nearby lines.
   5. FLOW & MELODY: Keep syllable count (±1) and rhyme scheme so the melody still fits.
   6. LENGTH: 6 to 9 syllables per edited line (±1).

F. FINAL SELF-CHECK (execute silently before outputting):
   - Count green lines: none missing, none changed, none repositioned.
   - Verify all present target words are still preserved.
   - Ensure each edited line passes goals 1 to 6 (including Standalone test and 6-9 syllables) and respects all Red Lines.
   - If a yellow line cannot be improved, keep it as is.

G. OUTPUT FORMAT:
   Part 1: The complete clean lyrics (without any [🔒], [🚨], or [⚠️] tags), ready to paste.
   Part 2: Change log, one line per edited line:
   "Original line" → "New line" | Reason for change
   (If nothing was edited, write "No edits needed".)
   
   === REVIEW ===
   Part 3: GREEN LINE REVIEW (suggestions only, NOT applied to Part 1).
   Check the green lines against goals E1 to E6, plus:
   - Flag any green line that breaks thematic consistency or setting continuity.
   - Is the line natural spoken English a learner can reuse in this setting?
   - Is the register (rude, formal, poetic, profane) flagged for the learner?
   - Any unclear "he" or "they", or a fact the speaker could not realistically know in the scene?
   - Is there weak coherence, forced rhyme, or repetition across the whole song?
   - Does any green line clash with an edit made in Part 1?
   Only mention a green line if you have a REAL, specific improvement. Do not pad the list. For each one give:
   "Original → Suggested | reason | priority (high / medium / low)"
   If nothing is worth changing, write "Green lines are solid, no suggestions."
   Finish with a verdict: overall coherence, educational value, and whether the song is ready to publish.

H. NEVER apply Part 3 suggestions to Part 1 unless the user explicitly approves them in the next message."""


def generate_master_prompt(
    target_words: List[str],
    genre: str,
    song_structure: str,
    mood_analysis: Dict[str, Any],
    creative_concept: str = "",
    selected_domain: str = "Basic / Neutral",
    vocalist: str = "Male",
    dialect: str = "American English"
) -> str:
    """
    Format a complete, production-ready Master Prompt ready to be copied into Claude / GPT-4o.
    Follows ESL-optimized songwriting methodology.
    """
    words_list_formatted = ", ".join(target_words)

    # Convert mood percentages to a descriptive string as per user instructions
    mood_items = sorted(
        mood_analysis.items(),
        key=lambda item: item[1] if isinstance(item[1], (int, float)) else 0,
        reverse=True
    )
    mood_str = ", ".join(k for k, v in mood_items if isinstance(v, (int, float)) and v > 0)
    if not mood_str:
        mood_str = "Casual, Conversational, Reflective"

    p = get_category_profile(selected_domain)

    story_text = creative_concept if creative_concept else p["default_story"]

    suno_style = build_suno_style_prompt(
        genre=genre,
        vocalist=vocalist,
        mood_analysis=mood_analysis,
        creative_concept=story_text,
    )

    structure_formatted = parse_song_structure(song_structure)

    chorus_rule = (
        "- Chorus: 4 short lines with one clear hook line. Repeat it identically every time; "
        "the Final Chorus may change one line for progression.\n"
    ) if "[Chorus]" in structure_formatted else ""

    domain_directive = p.get("domain_directive", "")
    domain_guidance_txt = f" {domain_directive}" if domain_directive else ""
    domain_target_rule = f"- Domain-specific guidance: {domain_directive}\n" if domain_directive else ""

    if selected_domain == "Science, Tech & Academia":
        target_words_philosophy = (
            "- HIGH VOCABULARY INTEGRATION BENCHMARK (14 to 17 words): In this technical/academic category, your benchmark is to naturally integrate at least 14 to 17 of the 20 target words into the collaborators' spoken dialogue.\n"
            "- STRICT PROHIBITION AGAINST LAZY SYNONYM REPLACEMENT: Never substitute a target word with a casual, generic synonym! For example, do NOT write 'make sure' when you have 'ensure'; do NOT write 'chance' when you have 'opportunity'; do NOT write 'this place' or 'here' when you have 'laboratory'; do NOT write 'enough' when you have 'sufficient'; do NOT write 'look at' or 'go through' when you have 'evaluate' or 'observe'; do NOT write 'aim' when you have 'objective'; do NOT write 'rules' when you have 'guideline'. Use the exact target words actively and authentically in their professional dialogue.\n"
            "- EDUCATED VOCABULARY IS NOT STIFF: Educated, professional terms in this field are natural spoken English for real researchers/specialists and do NOT violate Red Line 1. Drop a word ONLY as an absolute last resort if it genuinely cannot fit without distorting syntax or breaking the scene. Never drop words merely out of convenience or laziness.\n"
        )
    elif selected_domain == "Basic / Neutral":
        target_words_philosophy = (
            "- HIGH VOCABULARY INTEGRATION BENCHMARK (15 to 18 words): In this Basic / Neutral category, words are foundational, universal everyday vocabulary. They naturally fit into virtually ANY ordinary real-life scenario, conversation, or relationship story without forcing. Your benchmark is to naturally integrate at least 15 to 18 of the 20 target words into the characters' spoken dialogue.\n"
            "- MANDATORY ALTERNATIVE CONTEXT RETRY BEFORE DROPPING: Because these words represent core everyday English, there is almost always an authentic conversational place for them. Before dropping any word, you MUST try at least two different natural conversational contexts (e.g. a direct question between characters, a natural emotional reaction, a practical observation, or dialogue from another speaker).\n"
            "- BASIC EVERYDAY WORDS ARE NATURALLY CONVERSATIONAL: Common, foundational words are the bread and butter of fluent spoken English and do NOT violate Red Line 1. Drop a word ONLY as an absolute last resort if every possible conversational placement sounds distorted or breaks the story. Never drop basic words out of laziness, rush, or convenience.\n"
            "- STRICT PROHIBITION AGAINST LAZY SYNONYM REPLACEMENT: Never substitute a target word with an alternate word just to avoid fitting it. Use the exact target words directly in dialogue.\n"
        )
    elif selected_domain == "Emotions & Relationships":
        target_words_philosophy = (
            "- HIGH VOCABULARY INTEGRATION BENCHMARK (14 to 17 words): In this Emotions & Relationships category, your benchmark is to naturally integrate at least 14 to 17 of the 20 target words into the characters' spoken dialogue, confessions, questions, and reactions.\n"
            "- STRICT PROHIBITION AGAINST CLOCK-WATCHING OPENINGS: Never begin Verse 1 by stating an alarm or digital time ('It's 5:45 AM', 'At 8:30 in the morning'). Dive directly in media res into the human action, spoken dialogue, sensory tension, or immediate physical dilemma.\n"
            "- FULL EMOTIONAL FREEDOM (HONOR REAL HUMAN FEELINGS): Real life holds genuine heartbreak, quiet distance, unspoken regret, and bittersweet acceptance. If the story concept calls for sorrow, loss, or a difficult parting, do NOT sugarcoat it with a forced, cheerful Disney ending. Let the characters speak with honest vulnerability, dignified sorrow, or quiet strength.\n"
            "- CONVERSATIONAL VULNERABILITY OVER POETIC CLICHES: Keep lyrics tender, raw, and conversational. Emotional impact comes from honest, understated spoken lines that real human beings whisper or confess — not melodramatic greeting-card poetry.\n"
            "- STRICT PROHIBITION AGAINST LAZY SYNONYM REPLACEMENT: Never substitute a target word with an alternate word just to avoid fitting it. Use the exact target words directly in dialogue.\n"
        )
    else:
        target_words_philosophy = (
            "- The words are drawn randomly from a larger database. The goal is NOT to use all of them. The goal is a perfect song: natural lines and a connected story always come before word coverage.\n"
            "- Coverage is tracked across the whole song collection, and a separate verification step counts which target words were used and which extra database words appeared naturally. Do not chase a count.\n"
        )

    prompt = f"""# SONG DRAFT PROMPT (ESL LEARNING)

Write one original song for an English learner.

{ESL_GOAL_BLOCK}

The song tells one believable real-life story that fits the theme and uses the target words only where they sound natural.

## INPUTS
- Target words: {words_list_formatted}
- Theme: {selected_domain}
- Category guidance: Setting: {p['setting']}. Register: {p['register']}.{domain_guidance_txt}
- Story: {story_text}
- Genre: {genre}
- Mood: {mood_str}
- Dialect: {dialect}

## PRIORITY ORDER (when rules conflict)
1. Every line sounds natural and is something a real person would say.
2. The story is coherent and in order.
3. Clean rhyme and rhythm.
4. Target words.

## RED LINES (a song that crosses any of these FAILS, no matter how well it does elsewhere)
1. Awkward or stiff lines. Any line that sounds unnatural, distorted, inverted, overly poetic, or padded to fit a rhyme. If a native speaker would not say it, the song fails.
2. Breaking the story. Any line that does not belong to the one story, contradicts it, or sits outside the setting.
3. Abrupt jumps. Any sudden shift in time, place, speaker, or topic that the learner cannot follow.
4. Losing the educational value. The song must stay useful learning content: every line a real, reusable sentence. No empty emotional filler, vague imagery, or lines that teach nothing a learner could say in real life.
5. Unclear speakers. Any "he", "they", or fact that the speaker could not realistically know in the scene.

If a target word can only be used by crossing a red line, drop it. Red lines always beat word coverage.

## TARGET WORDS
{target_words_philosophy}{domain_target_rule}- Before dropping any word, first try to use it in a different context or story detail. Try at least two other natural contexts (a different speaker, a different line, a different angle on the scene).
- Drop a word only if every attempt sounds forced, awkward, or breaks the story.
- Never force a word in just for coverage.
- If a character's role matches a target word (for example, a "director" character and the word "director"), use it.
- Inflected forms are fine (plural, tense, "every day").
- Sensitive words (kill, terrorist, etc.) only in ordinary or figurative everyday use, otherwise skip.
- Use one consistent variety of English in the whole song. Never mix American and British forms.

## STORY RULES
- Strictly adhere to the established Story Concept: "{story_text}".
- STRICT NO-CLOCK OPENINGS: Never begin Verse 1 with a digital clock announcement (e.g. 'It's 5:45 AM', '8:30 on the clock'). Begin with dialogue, physical action, or evocative sensory tension in media res.
- Words First Principle: Target words must appear in their authentic, natural spoken meaning. The story scenario gives characters real, believable reasons to speak them; never distort a word's meaning or force awkward syntax.
- Every character who speaks or is mentioned must be named or clearly identified. No unexplained "he" or "they."
- One place, one continuous situation. Memories are allowed only if they directly support the conflict.
- Every line advances or deepens the story. No random imagery, no jumps outside it.

## LINE QUALITY RULES
- Line length: 5-9 syllables per line. Short punchy lines (4-5 syllables) are completely welcome for conversational reactions, exclamations, and dialogue hooks. Verses all have the same number of lines.
- Test every line: would a native speaker say this to the person in this scene? If not, rewrite it.
- No: poetic or abstract metaphors, inverted word order, filler to fit rhyme ("this way", "I'd say", "all along" as padding), stacked clichés.
- If a perfect rhyme forces an awkward line, use a near rhyme or rewrite both lines.
- Prefer direct sentences a learner can reuse in real life.

## CHORUS & SUNO RULES
{chorus_rule}- Write numbers as words. No parentheses, ad-libs, or sound effects inside lyrics.
- Avoid hard-to-pronounce words at the end of lines.

## SELF-CHECK (do silently, then fix before output)
For every line: natural? in story order? right length? dialect consistent? no filler? Is each target word used in its natural everyday meaning, not forced? For every word left out: did I try at least two other natural contexts before dropping it?
Standalone test: if this line is read alone, is it a natural, useful sentence a learner could say in real life?
Rewrite any line that fails.

## OUTPUT FORMAT
Output only the following. Do not print your plan, notes, or explanations.
Text in parentheses below are instructions about line counts. Never print them.

[Title]: ...
[Genre]: {genre}
[Suno Style]: {suno_style}

[Lyrics]:
{structure_formatted}

[Words used]: ...
[Words left out]: ...
"""
    return prompt


def build_song_audit_prompt(target_words: Optional[List[str]] = None) -> str:
    """Constructs the strict Song Audit Prompt for copy-pasting into external LLMs (Claude/ChatGPT)."""
    words_joined = ", ".join(target_words) if target_words else ""
    target_words_note = f"\n- Current Target Words to verify: {words_joined}\n" if words_joined else ""
    return f"""ممنوع الركاكة, محتوي تعليمي حقيقي لمتعلمين اللغة الانجليزية الي يحفظ سطر نتاكد انه سطر حقيقي بيتم استعماله في الحياة و سطر مشهور, الابتعاد عن السطور و الكلام المغمور الي في الكتب و الروايات الكلاسيكية, التركيز علي الانجليزي المتعارف عليه. و القصة مترابطة بدون وجود اي شذوذ فيها

# SONG AUDIT PROMPT (REFINEMENT SIEVE)

Audit the song above. Do not rewrite it yet. Be strict, honest, and objective.

STEP 1: LINE-BY-LINE TABLE

For every line (skip repeated Chorus and Pre-Chorus after the first time), output:

Line | Syllables (written out, e.g. fed-er-al = 3) | Total | Natural? | Speaker would know this? | Issue

Count syllables by writing each word’s syllables out. Never estimate.
Syllable Standard: 5-9 syllables per line. Short punchy dialogue lines (4-5 syllables) are completely fine and welcome for natural reactions, exclamations, and hooks (e.g. "There! The belt's back on!"). Flag lines ONLY if they are overcrowded (10+ syllables) or dragged out. NEVER flag or expand natural native contractions (such as turning "belt's" into "belt is") just to artificially add syllables.
“Natural?” means a native speaker would say this exact sentence to this person in this scene. Flag stiff, inverted, poetic, or padded lines.
“Speaker would know this?” means the character saying it could realistically know it at that point in the scene.

CRITICAL CRITIC ALIGNMENT (SITUATIONAL REGISTER & AUTHENTICITY):
The Strict Critic penalizes lines by 25 points for subtle register mismatches between the characters, setting, and wording. Ensure:
1. SCENARIO REGISTER FIT: Characters must speak in the exact register that naturally fits their relationship and setting. In casual/family scenes, dialogue must sound conversational and intimate (avoiding bureaucratic office jargon, news-broadcast melodrama, or clinical detachment). In professional, technical, or legal scenes, characters naturally use the authentic terminology of their field without artificial stiffening.
2. CONVERSATIONAL TARGET INTEGRATION: Target words must emerge naturally as genuine spoken statements, authentic reactions, questions, or dialogue between characters. Never tack on a target word as an artificial label, announcement, or awkward afterthought.
3. ORGANIC SENTENCE STRUCTURE (NO CHOPPED JUXTAPOSITION): Multiple target words in a single line are completely acceptable ONLY if they flow together in one coherent, natural sentence (e.g. "My daughter gave me great advice"). Never chop a line into disjointed, abrupt fragments just to fit words together.

STEP 2: STORY CHECK
Is it one place, one continuous situation, in time order? (Verses and Bridge develop linearly; Chorus is a recurring musical hook exempt from chronological plot timing).
Is every character named or clearly identified? Any unexplained “he” or “they”?
Does every line advance or deepen the story? Any sudden jump or contradiction?
Does the story use the scene details from the brief (setting, objects, atmosphere)?

STEP 3: DIALECT AND CLEANLINESS
Any American/British mixing (vocabulary, spelling, grammar)?
Any profanity or sensitive wording that is not an ordinary everyday expression?

STEP 4: TARGET WORDS (ANTI-LAZINESS & RESCUE AUDIT)
{target_words_note}For each target word, state: Used or Left out.

- Used: verify it is in its natural, everyday conversational meaning.
- Left out (PROTECT, RESCUE & JUSTIFY RULES):
  1. PROTECTION OF WORKING WORDS: Never drop a target word that was already working naturally in the previous draft just because you are editing adjacent lines. Preserving working words is mandatory.
  2. TARGET WORD RESCUE (IN-DRAFT WORDS): If a line containing a target word fails Step 1 (stiff, jargon, or syllable mismatch), fix the sentence structure using the Critic Alignment rules while keeping the target word, before deciding to drop it.
  3. ONE-SHOT RESCUE OPPORTUNITY FOR LEFT-OUT WORDS (ANTI-LAZINESS):
     - For every word currently listed in '[Words left out]', actively scan the draft for a conversational rescue opportunity:
       Can this word be seamlessly integrated into one of the lines being edited, or into a flat/generic line in the verses or bridge, using a common, high-frequency American spoken collocation (e.g. 'own' -> 'on your own' / 'your own place' / 'your own wall', 'seek' -> 'the peace you seek' / 'what you seek', 'allow' -> 'allow me to help' / 'if time allows', 'maker' -> 'coffee maker' / 'the maker built it')?
     - If a 100% natural, everyday spoken opportunity exists without any awkwardness or stuffing, formulate the revision and integrate the word into [Words used]!
     - REJECTION OF LAZY DISQUALIFICATIONS: Never accept dismissive excuses like "it would be filler" or "it is formal" for foundational everyday words if a genuine conversational collocation fits the scene naturally.
  4. LEGITIMATE PERMANENT DROP (RED LINES ALWAYS BEAT WORD COVERAGE):
     - If a word truly cannot fit without violating Red Line 1 (awkward syntax, distorted dialogue, or hyper-technical terms like 'equivalent' that native speakers would never say in this scene), state the exact 1-sentence incompatibility reason.
     - Once a word is legitimately verified as incompatible with natural dialogue, it remains permanently dropped. NEVER force or distort lines just to chase a 20/20 count. Natural spoken lines always come first.

STEP 5: VERDICT & CONVERGENCE (STOPPING CRITERION)

- If ANY line has genuine issues (overcrowded 10+ syllables, unnatural syntax, story contradiction, or Critic traps) OR an unused target word can be naturally integrated via Step 4.3:
  * List every failing or upgraded line with its one-line fix.
  * Give verdict: FAIL (Issues identified or vocabulary upgraded, applying fixes).
  * Output the revised song in the original format, fixing ONLY the necessary lines and keeping all passing lines and working target words strictly intact.

- CONVERGENCE & STOPPING CRITERION (PREVENTING INFINITE LOOPS):
  * The goal is a natural, memorable song with strong vocabulary integration (15 to 18 words), NOT an unnatural 20/20 forced cram.
  * If ALL lines in the song are already within natural rhythm (4-9 syllables), 100% natural spoken American English (zero Critic traps), story-consistent, and all remaining left-out words are legitimately incompatible without forcing:
  * DO NOT invent cosmetic rewrites, do NOT loop endlessly, and do NOT attempt to force incompatible words.
  * You MUST declare: VERDICT: PASS (READY FOR SUNO PRODUCTION).
  * Output the final song cleanly without alterations.


Keep the response concise. No long philosophical explanations.
Write explanations in Arabic, keep lyrics in English.
متحرقش كلام كتير في الرد، كفاية التعديلات (السابق والجديد) والنسخة المحدثة فقط في البورد علشان ألزقه براحتي.
"""

