"""
constants.py — Fixed lists and configurations for Audingo Songs Forge.
"""

import logging
import random
logger = logging.getLogger(__name__)

# Fixed list of music genres — curated for educational songwriting where
# vocal clarity is paramount. Every genre here guarantees upfront, clear vocals.
GENRES = [
    "Pop",
    "K-Pop Style (Clear English Vocals)",
    "Synth-Pop / 80s Retro",
    "Indie Pop",
    "Acoustic / Folk",
    "R&B / Contemporary Soul",
    "Country / Americana",
    "Funk / Disco Groove",
    "Reggae / Tropical Pop",
    "Jazz / Bossa Nova",
    "Cinematic / Ballad",
    "Lo-Fi / Chillhop",
    "Melodic Chill Electronic"
]

# Fixed list of song structures
SONG_STRUCTURES = [
    "Verse - Chorus - Verse - Chorus - Bridge - Chorus - Outro",
    "Verse - Pre-Chorus - Chorus - Verse - Pre-Chorus - Chorus - Bridge - Chorus",
    "Intro - Verse - Chorus - Verse - Chorus - Outro",
    "AABA (Verse - Verse - Bridge - Verse)",
    "Verse - Chorus - Verse - Chorus - Chorus",
    "Through-Composed (Story-driven, no repeating chorus)"
]

# Mood and sentiment categories
MOOD_CATEGORIES = [
    "Happy",
    "Energetic",
    "Uplifting / Inspiring",
    "Romantic / Sweet",
    "Chill / Relaxed",
    "Nostalgic / Melancholic",
    "Sad / Heartbroken",
    "Dark / Moody",
    "Dramatic / Intense",
    "Playful / Quirky"
]

# Supported Gemini models for routine studio tasks (prioritizing fast/efficient models to preserve top models for critic)
GEMINI_MODEL_CANDIDATES = [
    "models/gemini-3.5-flash",
    "models/gemini-3.5-flash-lite",
    "models/gemini-3.1-flash-lite",
    "models/gemini-flash-latest",
    "models/gemini-3.6-flash",
    "models/gemini-3.7-flash",
    "models/gemini-3.8-flash",
]

# 6 Core NGSL Vocabulary Domains (COCA Frequency Based)
DOMAINS = [
    "Basic / Neutral",
    "Science, Tech & Academia",
    "Emotions & Relationships",
    "Street & Daily Life",
    "Law, Politics & Society",
    "Business & Career"
]

DOMAIN_CONFIG = {
    "Basic / Neutral": {
        "emoji": "🃏",
        "color": "var(--studio-amber)",
        "bg": "rgba(245, 158, 11, 0.15)",
        "border": "rgba(245, 158, 11, 0.4)",
        "label_ar": "الجوكر (كلمات عامة وأساسية)"
    },
    "Science, Tech & Academia": {
        "emoji": "🔬",
        "color": "var(--studio-teal)",
        "bg": "rgba(6, 182, 212, 0.15)",
        "border": "rgba(6, 182, 212, 0.4)",
        "label_ar": "العلوم والتقنية والأكاديميا"
    },
    "Emotions & Relationships": {
        "emoji": "❤️",
        "color": "var(--studio-pink)",
        "bg": "rgba(244, 63, 94, 0.15)",
        "border": "rgba(251, 113, 133, 0.4)",
        "label_ar": "المشاعر والروايات"
    },
    "Street & Daily Life": {
        "emoji": "🏙️",
        "color": "var(--studio-green)",
        "bg": "rgba(16, 185, 129, 0.15)",
        "border": "rgba(52, 211, 153, 0.4)",
        "label_ar": "الشارع واليوميات"
    },
    "Law, Politics & Society": {
        "emoji": "🏛️",
        "color": "var(--studio-purple)",
        "bg": "rgba(139, 92, 246, 0.15)",
        "border": "rgba(167, 139, 250, 0.4)",
        "label_ar": "القانون والسياسة والمجتمع"
    },
    "Business & Career": {
        "emoji": "💼",
        "color": "var(--studio-blue)",
        "bg": "rgba(59, 130, 246, 0.15)",
        "border": "rgba(96, 165, 250, 0.4)",
        "label_ar": "العمل والبيزنس"
    }
}

# --- Category Profiles for Prompts & Critics ---

CASUAL = "casual spoken English, the way people talk to friends and family"

FIELD = (
    "natural spoken English as real people use it in that field (meetings, labs, courts, newsrooms): "
    "plain words, contractions are normal, technical terms only when real speakers say them. "
    "Never textbook, dictionary or document-style sentences"
)

CATEGORY_PROFILES = {
    "Basic / Neutral": {
        "setting": "any ordinary situation that fits the words",
        "register": CASUAL,
        "default_story": "A relatable everyday story grounded in real conversation between real people.",
        "critic_name": "🃏 General Critic",
        "props": [
            "a cutting board with sliced lemons and a kitchen knife",
            "a garden hose coiled on sun-warmed driveway concrete",
            "a set of house keys jingling on a wooden hall table",
            "a receipt folded in a worn leather wallet",
            "an umbrella dripping onto a doormat in the hallway",
            "a cardboard coffee tray with three takeaway cups on a car dashboard",
            "a winter coat hung over the back of a kitchen chair",
            "a toolbox open on the garage floor with wrenches sorted",
            "a paper road map with highlighter marks in the glove box",
            "a backpack unzipped on the kitchen table with notebook corners showing",
            "a small battery radio playing quietly on a porch windowsill",
            "a half-assembled bookshelf and scattered hardware on a rug",
            "a canvas grocery tote filled with fresh produce on the counter",
            "a framed family picture catching afternoon window light",
        ],
        "times": [
            "Early morning at 6:45 AM, kettle whistling, first gray light through kitchen blinds",
            "A busy Saturday 10:30 AM, neighborhood sidewalks bustling with weekend errands",
            "A quiet Sunday afternoon at 2:00 PM, warm sunlight through a living room window",
            "Late afternoon 4:45 PM, packing bags and catching the commute home",
            "Sunset at 6:30 PM on a front porch, streetlights beginning to flicker on",
            "Dinner table at 8:15 PM, shared food and steam rising from plates",
            "Quiet late night at 11:30 PM, house asleep, gentle rain on the glass",
            "A midnight highway drive, glowing dashboard, headlights cutting through empty miles",
        ],
        "character_setups": [
            {
                "type": "duo_dialogue",
                "label": "Two close friends or family in direct conversation",
                "instruction": "Two clearly named people speak face to face. Their mutual trust and dynamic drive every line.",
                "weight": 40,
            },
            {
                "type": "solo_narrator",
                "label": "One person reflecting on an everyday turning point",
                "instruction": "A single narrator reflects on their day, a choice they made, or a quiet realization. Introspective, candid, personal.",
                "weight": 20,
            },
            {
                "type": "roommates_family",
                "label": "Roommates or household members in a shared routine",
                "instruction": "Two or three people managing a household moment together — cooking, cleaning, budgeting, or planning.",
                "weight": 15,
            },
            {
                "type": "neighbor_encounter",
                "label": "Two neighbors crossing paths in the neighborhood",
                "instruction": "An informal, grounded exchange between neighbors on a porch, driveway, lawn, or sidewalk.",
                "weight": 10,
            },
            {
                "type": "stranger_moment",
                "label": "Two travelers or patrons sharing an unexpected candid talk",
                "instruction": "Two people waiting for transit or seated nearby who share an honest moment before parting ways.",
                "weight": 10,
            },
            {
                "type": "remote_call",
                "label": "A phone call or voice message checking in across distance",
                "instruction": "Someone calling a loved one to check in, share news, or talk through a worry across miles.",
                "weight": 5,
            },
        ],
        "arcs": [
            {
                "name": "Classic Resolution",
                "arc": "Problem or doubt -> candid conversation -> quiet determination to move forward together",
                "ending_flavor": "Characters find practical peace and a shared next step.",
                "weight": 18,
            },
            {
                "name": "Bittersweet Acceptance",
                "arc": "Recognizing that life circumstances have changed -> quiet realization -> grace without resentment",
                "ending_flavor": "Nobody fixes the past; they accept what is with dignity and warmth.",
                "weight": 18,
            },
            {
                "name": "Everyday Teamwork Hurdle",
                "arc": "Sudden daily breakdown (flat tire, leaky pipe, missed bus) -> teamwork -> laughing it off together",
                "ending_flavor": "Light, warm, resilient. The mishap is solved and the bond is stronger.",
                "weight": 16,
            },
            {
                "name": "Quiet Personal Resilience",
                "arc": "Navigating a tough personal week -> standing steady -> small private victory",
                "ending_flavor": "No grandiose drama; just one person proving they have what it takes to keep going.",
                "weight": 14,
            },
            {
                "name": "Mutual Celebration",
                "arc": "Earning a modest milestone or good news -> sharing the moment -> genuine gratitude",
                "ending_flavor": "Unapologetically positive and joyful, celebrating a real-life accomplishment.",
                "weight": 12,
            },
            {
                "name": "Heartfelt Goodbye",
                "arc": "An unavoidable departure or relocation -> final spoken wishes -> watching them leave",
                "ending_flavor": "The departure is real and final, held with deep respect and fond memories.",
                "weight": 12,
            },
            {
                "name": "Generational Bridge",
                "arc": "Misunderstanding across ages -> finding unexpected common ground -> mutual respect",
                "ending_flavor": "Both sides listen and learn something genuine from the other.",
                "weight": 10,
            },
        ],
        "story_settings_examples": [
            "Everyday home, neighborhood, or shared social setting",
            "A casual morning walk, garden bench, or phone call between close friends",
            "Kitchen table on a Sunday evening planning a weekly budget or sorting utility bills",
            "Neighborhood driveway or garage on a sunny Saturday morning fixing a lawnmower or car with a neighbor",
            "Subway platform or commuter train during a delay where two travelers share an honest talk",
            "Hardware store aisle or home workshop figuring out the right tools for a weekend DIY repair",
            "Laundromat on a weekday afternoon, waiting for dryers while trading news about work and family",
            "Community garden plot or neighborhood park trail walking a dog at 8:00 AM",
            "Supermarket checkout line dealing with a runaway cart, forgotten coupon, or spilled groceries",
            "Afternoon highway road trip or rest stop, talking through a life-changing decision between two friends",
            "Front porch or apartment balcony at sunset sharing takeout while unwinding after a tough week",
            "Rainy roadside gas station waiting out a sudden summer downpour while grabbing a quick drink",
            "Quiet hospital clinic waiting room at 10:00 AM, whispering comfort while waiting for routine test results",
            "Empty train station platform at dawn, watching taillights pull away after a heartfelt farewell",
            "Kitchen counter preparing Sunday breakfast together, working through an awkward misunderstanding",
            "Workplace breakroom between morning and afternoon shifts, two colleagues sharing lunch and family advice",
        ],
        "story_conflict_archetypes": [
            "A relatable personal dilemma, decision, or shared moment between friends or family",
            "Overcoming a daily obstacle through mutual support and clear communication",
            "Two friends resolving an awkward miscommunication over loaned money or an unkept promise with honest words",
            "Roommates or partners negotiating domestic chores and personal space without turning it into an argument",
            "A neighbor offering unexpected hands-on help when another is overwhelmed by a sudden household breakdown",
            "Two friends reconciling after a prolonged falling out, putting pride aside to speak the truth",
            "A person wrestling with whether to take a modest life risk (moving, changing routine) and seeking candid advice",
            "Overcoming unexpected daily frustration (bad weather, flat tire, missed bus) by laughing it off together",
            "Processing quiet grief or deep personal loss with honest, comforting words between close loved ones",
            "A painful but unavoidable parting between close friends or family due to distance, career, or life paths",
            "Coming to terms with a shattered plan without anger, finding solace in quiet acceptance",
            "Supporting an aging parent or friend through changing health, balancing sorrow with gentle tenderness",
            "Dealing with quiet loneliness or homesickness in an unfamiliar city, reaching out across the miles",
            "Struggling with burnout in a daily routine, finding courage through a loved one's honest perspective",
            "A parent and grown child at a breakfast table, bridging a long-standing generational misunderstanding",
            "Two coworkers handling an unexpected blunder before the morning shift starts, backing each other up",
        ],
        "domain_directive": (
            "Use clear, natural spoken English suitable for everyday life. "
            "Prioritize conversational dialogue that any native speaker would say to a friend. "
            "Because these words are universal, foundational everyday terms, integrate them actively into characters' dialogue, questions, and reactions. "
            "FULL EMOTIONAL SPECTRUM: Real everyday life encompasses deep sorrow, painful goodbyes, quiet grief, and poignant nostalgia just as much as lighthearted moments. "
            "Do NOT shy away from sad or bittersweet scenarios when the words or mood suggest it; treat sadness as an authentic, profound pillar of everyday human experience. "
            "CREATIVE EXPANSION: Draw from the full, vibrant spectrum of human environments across every hour of the day. "
            "INVENT, DO NOT COPY: The setting and conflict examples are structural springboards, never a fixed menu to copy mechanically. "
            "Observe the underlying human patterns and invent a fresh, original real-life scenario tailored uniquely to the given words."
        ),
    },
    "Science, Tech & Academia": {
        "setting": "lab, classroom, study group, tech team, research project",
        "register": FIELD,
        "critic_guidance": (
            "Accept moderately formal, educated spoken English in this category; street slang is not the standard. "
            "Judge the actual story, including personal or family scenes involving academic or technical lives; "
            "the suggested settings are examples, not mandatory locations. "
            "Do not deduct merely because storage, assumption, connect, scientist, university, input, database, "
            "necessary, analysis, or progress sounds academic, technical, or professional. "
            "For example, 'These files sat in archive for years.', 'I made a bad assumption.', "
            "'He taught at the university.', 'He always wanted my input,' and 'Not everything needs analysis.' "
            "can be natural in a family reflection. These are calibration examples, not guaranteed scores. "
            "Technical vocabulary does not inherently break an emotional mood. "
            "Still flag a genuinely wrong meaning, unnatural collocation, unclear reference, or unsupported story jump; "
            "explain the specific problem rather than calling a word formal, clinical, or corporate."
        ),
        "default_story": "A relatable story set in a lab, classroom, or tech team facing a real challenge together.",
        "critic_name": "🔬 Science & Tech Critic",
        "props": [
            "a dual-monitor terminal flashing lines of telemetry logs",
            "a spiral lab notebook with handwritten chemical formulas and coffee rings",
            "a pipette rack and chilled sample vials in a centrifuge tray",
            "a server rack humming with pulsing blue and amber LEDs",
            "a cracked microscope slide under an adjustable halogen lamp",
            "a whiteboard filled with architectural flowcharts and half-erased equations",
            "a laser measurement device and marked blueprint rolls on a drafting desk",
            "a 3D-printed prototype chassis with exposed ribbon cables",
            "a telemetry tablet showing fluctuating sensor readings in real time",
            "a badge lanyard tangled around laser safety goggles on a bench",
            "an encrypted thumb drive sitting beside a capstone thesis binder",
            "a field soil sample kit and GPS logger in a weather-sealed case",
            "an astronomy monitor feed showing anomalous celestial telemetry",
            "a calibration torque wrench on an experimental hardware test rig",
        ],
        "times": [
            "3:15 AM in a quiet lab, servers humming, automated test suites running",
            "8:00 AM before the morning symposium kickoff, hurried slide checks over tea",
            "11:30 AM collaborative peer review, team gathered around a terminal",
            "2:30 PM mid-afternoon experiment run, waiting for incubator readouts",
            "5:45 PM wrap-up debrief, comparing unexpected anomalies against baseline hypotheses",
            "Dusk at an ecology field station, weather gear unpacked as storms roll in",
            "10:00 PM sprint war-room, whiteboard covered in patches before software deploy",
        ],
        "character_setups": [
            {
                "type": "duo_collaborators",
                "label": "Two researchers or engineers in active collaboration",
                "instruction": "Two colleagues analyze data, debate an interpretation, or troubleshoot a failing system face to face.",
                "weight": 40,
            },
            {
                "type": "mentor_apprentice",
                "label": "Principal investigator and a graduate researcher",
                "instruction": "An experienced scientist guides a junior colleague through imposter syndrome or a difficult methodological choice.",
                "weight": 20,
            },
            {
                "type": "sprint_team",
                "label": "A multidisciplinary team tackling a live incident",
                "instruction": "Engineers, analysts, and project leads coordinating under pressure to fix a critical issue.",
                "weight": 15,
            },
            {
                "type": "solo_specialist",
                "label": "A lone researcher narrating a breakthrough or setback",
                "instruction": "One specialist working through anomalous findings, reflecting on the human impact of their discovery.",
                "weight": 15,
            },
            {
                "type": "cross_disciplinary_debate",
                "label": "Two specialists from different fields resolving a conflict",
                "instruction": "A hardware architect and software engineer, or clinical doctor and data scientist, bridging their viewpoints.",
                "weight": 10,
            },
        ],
        "arcs": [
            {
                "name": "Empirical Breakthrough",
                "arc": "Months of erratic data -> systematic elimination of errors -> the numbers finally align",
                "ending_flavor": "Excitement grounded in rigorous proof and quiet professional pride.",
                "weight": 20,
            },
            {
                "name": "Grace in Negative Results",
                "arc": "Hypothesis fails under testing -> admitting the outcome without evasion -> discovering a better question",
                "ending_flavor": "Scientific integrity shines. Failure becomes the catalyst for real understanding.",
                "weight": 18,
            },
            {
                "name": "Racing the Clock",
                "arc": "System anomaly or deadline crunch hours away -> focused triage -> patch deployed just in time",
                "ending_flavor": "Exhausted relief and mutual high-fives as monitors turn green.",
                "weight": 18,
            },
            {
                "name": "Ethical Balance",
                "arc": "Commercial pressure to release early -> discovering an algorithmic flaw -> taking a principled stand for safety",
                "ending_flavor": "Integrity wins over convenience; the team agrees to fix it properly.",
                "weight": 16,
            },
            {
                "name": "Passing the Torch",
                "arc": "Junior researcher doubts their capability -> mentor steps back -> apprentice presents the winning solution",
                "ending_flavor": "Generational pride and confidence earned through real mastery.",
                "weight": 14,
            },
            {
                "name": "Uncovering the Hidden Flaw",
                "arc": "A stubborn bug baffles everyone -> re-examining the simplest baseline assumption -> fixing it together",
                "ending_flavor": "Humbling lesson that simplicity and clear communication beat complex over-engineering.",
                "weight": 14,
            },
        ],
        "story_settings_examples": [
            "University research laboratory working on an experimental run before a grant deadline",
            "Tech startup open office troubleshooting a critical backend bug before public launch",
            "Robotics workshop or engineering bench testing a physical prototype under load",
            "Medical diagnostic lab or clinical study reviewing complex patient data",
            "Campus library or study lounge where graduate students prep for a capstone defense",
            "Field ecology station or marine survey vessel logging environmental telemetry",
            "Cybersecurity operations center at 2:00 PM responding to an anomalous network spike",
            "Radiology or pathology suite, two specialists comparing high-resolution scans",
            "Architecture drafting studio surrounded by structural models and load calculations",
            "Astronomy observatory control room at dawn, logging telescope telemetry",
            "Pharmaceutical trial review meeting, balancing safety protocols against development timelines",
            "Faculty office in the afternoon, mentor and student re-evaluating thesis hypotheses",
            "Meteorology tracking center during an approaching weather system, checking radar feeds",
            "Archaeological field tent in the late afternoon, cataloging fragile findings",
            "Classroom bench after a failed lab demonstration, instructor walking an apprentice through error diagnostics",
        ],
        "story_conflict_archetypes": [
            "Two researchers racing the clock when test results vary wildly hours before a submission",
            "A software engineer and team lead debating whether to rewrite core logic or push a quick patch",
            "A specialist and an apprentice discovering an unexpected flaw in their initial assumptions",
            "Colleagues pushing through exhaustion, pooling their knowledge, and celebrating a hard-won discovery",
            "Defending unconventional experimental findings before a skeptical review panel with calm rigor",
            "A data analyst and project lead clashing over whether user metrics ethically justify changing an algorithm",
            "Field researchers confronting equipment failure in harsh wilderness and relying on manual calculations",
            "A mentor helping a talented student overcome imposter syndrome before delivering a major conference paper",
            "Balancing commercial pressure for speed against uncompromising scientific safety standards",
            "A medical team wrestling with whether to publish a negative trial result that disproves their own hypothesis",
        ],
        "domain_directive": (
            "Accept educated, professional spoken English (collegiate, tech, lab, or clinical dialogue); street slang is NOT the standard. "
            "Anchor target words in active spoken dialogue between collaborators (e.g. 'demonstrate the fix', 'we need a specialist', "
            "'the error is constant', 'results vary between tests', 'don't be too critical', 'describe what failed', 'that occupies my time'). "
            "Do NOT drop academic or technical words simply because they sound educated; native speakers use them constantly in these settings. "
            "CREATIVE EXPANSION: Draw from the broad spectrum of scientific and technical human endeavors. "
            "INVENT, DO NOT COPY: The setting and conflict examples are structural springboards, never a fixed menu to copy mechanically."
        ),
    },
    "Emotions & Relationships": {
        "setting": "a real emotional moment between family, friends, partners, or estranged loved ones",
        "register": CASUAL,
        "default_story": "A deeply human story exploring honest vulnerability, poignant turning points, or unexpected emotional truth.",
        "critic_name": "❤️ Emotions Critic",
        "props": [
            "a handwritten letter found tucked inside an old book years later",
            "a framed photograph with a cracked corner on an otherwise empty mantelpiece",
            "two taped cardboard moving boxes sitting on bare hardwood floors",
            "a phone screen lighting up silently on the passenger seat in the dark",
            "a set of old house keys placed quietly on a dining room table",
            "a worn flannel shirt carrying a scent that instantly sparks a memory",
            "two paper cups cooling untouched on a concrete bench in the cold",
            "a ticket stub from a journey taken together that never happened again",
            "an umbrella tilted in the driving rain to shelter someone else's shoulders",
            "a silver chain or ring turning between restless fingers during a difficult talk",
            "a cassette tape or playlist titled with an inside joke from years ago",
            "a hospital or clinic waiting room pass crumpled in a coat pocket",
            "a porch light left burning into the twilight for someone who hasn't arrived",
            "a car windshield fogging up while sitting in a quiet gravel driveway",
            "a half-packed suitcase lying open across a bed with clothes neatly folded",
        ],
        "times": [
            "A rain-slicked highway at dusk, wipers rhythmic against the quiet car cabin",
            "Late night on an empty porch under distant rolling thunder, cold tea on the railing",
            "A grey Sunday afternoon in a quiet apartment surrounded by moving boxes",
            "Dawn fog clinging to an empty gravel parking lot outside a 24-hour diner",
            "Midday rush on a loud train station platform, watching one figure disappear into the crowd",
            "A cold November evening under buzzing amber streetlights with breath visible in the air",
            "Early twilight before sunrise, sitting alone with words that cannot be undone",
            "An overcast morning by a coastal pier, salt wind blowing cold against coats",
            "Midnight in a dimly lit kitchen, speaking in hushed tones so no one else wakes",
            "A humid summer twilight on fire escape metal stairs, city traffic humming below",
            "A bitter winter afternoon standing by the open trunk of an idling car on the road shoulder",
            "The quiet stillness right after the front door clicks shut and footsteps fade away",
        ],
        "character_setups": [
            {
                "type": "the_irreversible_crossroads",
                "label": "Two people realizing their paths must permanently diverge",
                "instruction": "A mature, heartbreaking recognition that love is not enough to bridge two incompatible futures. No villain, just life.",
                "weight": 20,
            },
            {
                "type": "estranged_siblings_or_family",
                "label": "Estranged siblings or family members confronting years of silence",
                "instruction": "Old defensive walls crumble during a crisis or shared milestone; painful honesty meets unspoken family loyalty.",
                "weight": 18,
            },
            {
                "type": "solo_coping_with_absence",
                "label": "Solo reflective narrator coping with sudden loss, grief, or memory",
                "instruction": "One person processing the physical silence left by someone who passed or walked away forever; finding strength in remembrance.",
                "weight": 16,
            },
            {
                "type": "partners_raw_breakthrough",
                "label": "Partners in a defining, raw confrontation breaking through fake politeness",
                "instruction": "Shattering weeks of guarded silence to speak the terrifying, necessary truth face to face.",
                "weight": 16,
            },
            {
                "type": "long_lost_reunion_twist",
                "label": "Two former close friends or lovers crossing paths years later by chance",
                "instruction": "An unexpected encounter in a transit hub or street corner; the sudden flood of memories and the sting of who they used to be.",
                "weight": 12,
            },
            {
                "type": "parent_adult_child",
                "label": "An adult child and an aging parent addressing the passage of time",
                "instruction": "Reversing roles of care, acknowledging unspoken sacrifices, and confronting the fragility of life with deep love.",
                "weight": 10,
            },
            {
                "type": "the_unspoken_longing",
                "label": "Two friends carrying feelings that were never spoken aloud",
                "instruction": "Standing on the edge of confession before an impending move or marriage, wrestling with the fear of ruining the friendship.",
                "weight": 8,
            },
        ],
        "arcs": [
            {
                "name": "The Irreversible Goodbye",
                "arc": "Holding on to hope -> facing the painful reality that it's over -> letting go with dignified, sorrowful gratitude",
                "ending_flavor": "No screaming or bitterness. The heavy, quiet ache of closing a chapter that meant everything.",
                "weight": 18,
            },
            {
                "name": "The Unspoken Regret",
                "arc": "Carrying words of apology or love for months -> waiting too long for the 'right time' -> the moment passes and distance remains",
                "ending_flavor": "Bittersweet melancholy; learning that pride costs more than vulnerability.",
                "weight": 16,
            },
            {
                "name": "The Sudden Revelation",
                "arc": "Comfortable assumptions about the past -> discovering a hidden truth or letter -> an emotional shock that reframes everything",
                "ending_flavor": "A dramatic turning point; tears of understanding replacing years of quiet resentment.",
                "weight": 16,
            },
            {
                "name": "Coping with the Empty Room",
                "arc": "Stunned paralysis from sudden absence -> small sensory reminders breaking through -> finding courage to carry their memory forward",
                "ending_flavor": "Poignant, dignified sorrow; love enduring long after the physical presence is gone.",
                "weight": 14,
            },
            {
                "name": "Raw Confrontation to Honest Healing",
                "arc": "Simmering resentment behind polite masks -> explosive, unfiltered honesty -> exhausted relief and tentative mutual respect",
                "ending_flavor": "The storm has cleared; the air is cold and clean, and genuine rebuilding can finally begin.",
                "weight": 14,
            },
            {
                "name": "Tender Confession of Long-Hidden Truth",
                "arc": "Paralyzing fear of rejection -> taking the leap of total vulnerability -> being met with unexpected warmth and acceptance",
                "ending_flavor": "Trembling relief, radiant intimacy, and the freedom of being completely seen.",
                "weight": 12,
            },
            {
                "name": "Quiet Solidarity in Grief",
                "arc": "A tragedy or setback too deep for words -> a companion arrives without advice or cliches -> sitting quietly together in the dark",
                "ending_flavor": "Comfort found not in fixing what cannot be fixed, but in not having to survive it alone.",
                "weight": 10,
            },
        ],
        "story_settings_examples": [
            "Rain-slicked gravel rest stop on an interstate highway at dusk with headlights sweeping past",
            "Empty apartment hallway with two taped cardboard boxes and a set of keys left on the counter",
            "Hospital or clinic waiting corridor at night, two people sharing coffee from a vending machine",
            "Cold train station platform as the final boarding announcement echoes through the mist",
            "Childhood bedroom with bare walls and furniture indentations in the carpet before the house is sold",
            "Car idling on a gravel driveway in the rain, windshield fogged, waiting for someone to speak",
            "Wind-whipped coastal ferry deck in November watching the island shoreline drift away",
            "Supermarket parking lot at closing time, sitting on the car hood under humming sodium lights",
            "Dusty attic kneeling over an open cedar trunk filled with old photographs and unsent postcards",
            "Kitchen table late at night, bills pushed aside, two mugs of cold tea and an opened letter",
            "Porch steps of an old family house in autumn twilight after the gathering has emptied out",
            "Airport baggage claim carousel circling endlessly as the last passengers take their bags and leave",
            "Small diner booth at 1:00 AM, salt shaker turning between anxious fingers during a difficult talk",
            "Wooden dock on a dark lake with water lapping against the pilings and distant thunder rumbling",
            "Laundromat hum in the late evening, two estranged friends folding clothes in awkward silence",
        ],
        "story_conflict_archetypes": [
            "Coming to terms with a deep love or friendship that has run its course without any villain or betrayal",
            "Delivering news that will change someone's life forever, wrestling with cowardice before speaking",
            "Clearing out a childhood home together after an irreversible loss, unearthing forgotten family fractures",
            "Apologizing for words spoken during an argument years ago that permanently altered the relationship",
            "Facing the first milestone, anniversary, or holiday alone after a sudden separation or death",
            "Wrestling with whether to confess long-harbored romantic feelings before a close friend moves across the country",
            "Reconnecting with an estranged sibling when a family crisis leaves no room for old grudges",
            "Choosing between a lifelong dream in another city and staying beside someone who cannot follow",
            "Discovering that a partner or friend was carrying a heavy secret alone to protect you from pain",
            "A parent and adult child finally acknowledging past mistakes and extending unconditional forgiveness",
        ],
        "domain_directive": (
            "STRICT IN-MEDIA-RES OPENING MANDATE: NEVER begin an Emotions song by checking a clock, reading an alarm, or declaring a digital time (e.g. 'It's 5:45 AM', 'At 8:30 in the morning'). Dive directly into the physical human action, direct spoken dialogue, sensory tension, or immediate emotional crossroads. "
            "FULL EMOTIONAL PALETTE (EMBRACE SADNESS, BITTERSWEET TRUTH & SURPRISE): Do not force every song into a neat, cheerful, cozy Disney ending! Real relationships hold genuine grief, painful partings, shocking revelations, and bittersweet acceptance. Let deep sorrow and emotional stakes breathe with dignity, restraint, and poetic power. "
            "CONVERSATIONAL AUTHENTICITY OVER CLICHES: Keep lyrics tender, raw, and conversational. Emotional impact comes from honest, understated spoken lines that real human beings whisper, stammer, or confess — not melodramatic greeting-card poetry. "
            "INVENT, DO NOT COPY: The settings and arcs are structural springboards; invent fresh, vivid, unforgettable moments tailored directly to the vocabulary."
        ),
    },
    "Street & Daily Life": {
        "setting": "streets, neighborhoods, errands, friends hanging out",
        "register": CASUAL,
        "default_story": "A relatable real-life story about people handling daily life and social moments.",
        "critic_name": "🏙️ Street Life Critic",
        "props": [
            "a plastic grocery bag full of oranges splitting at the handle",
            "a pair of worn work boots drying by a radiator",
            "an umbrella blown inside-out on a windy street corner",
            "a steel tape measure and utility knife on a leather tool belt",
            "a grease-stained auto repair receipt on a shop counter",
            "a stack of delivery parcels balanced on a mail carrier cart",
            "a chrome diner napkin dispenser and glass salt shaker",
            "a bicycle lock key on a coiled neon keychain",
            "an aluminum takeout container of grilled food steam-fogging the lid",
            "a rubber squeegee and soapy water bucket at a gas station island",
            "a pair of electric barber clippers buzzing on an acrylic tray",
            "a scuffed basketball bouncing on a chain-link asphalt court",
            "a subway metro card held ready at a busy turnstile gate",
            "two gallon cans of interior latex paint and wooden stir sticks",
        ],
        "times": [
            "6:00 AM corner bakery opening, smells of warm bread and diesel exhaust",
            "8:15 AM rush hour sidewalk, crowds moving briskly toward turnstiles",
            "Noon lunch rush at a food cart, steam rising, coins clinking on the counter",
            "3:30 PM school dismissal on a residential avenue, crossing guards and chatter",
            "5:45 PM packed commuter bus, brakes squealing as evening traffic crawls",
            "8:00 PM dusk pickup game at the blacktop court, streetlamps humming on",
            "1:30 AM fluorescent-lit 24-hour laundromat, dryers tumbling rhythmically",
        ],
        "character_setups": [
            {
                "type": "duo_dialogue",
                "label": "Two neighbors, coworkers, or regulars on the block",
                "instruction": "Two everyday people shooting the breeze on a stoop, sidewalk, or shop counter.",
                "weight": 40,
            },
            {
                "type": "commuter_comrades",
                "label": "Strangers sharing a laugh over a transit delay or mishap",
                "instruction": "Commuters bonding over an unexpected shared inconvenience with wry humor and patience.",
                "weight": 20,
            },
            {
                "type": "shopkeeper_regular",
                "label": "A neighborhood vendor and familiar customer trading news",
                "instruction": "Warm, authentic community rapport between someone behind the counter and a local patron.",
                "weight": 15,
            },
            {
                "type": "working_shift_partners",
                "label": "Two service or trades workers tackling a long physical shift",
                "instruction": "Mutual hustle, dark humor, and teamwork to get through an exhausting workday.",
                "weight": 15,
            },
            {
                "type": "solo_neighborhood_observer",
                "label": "Solo person narrating the rhythm and grit of their neighborhood",
                "instruction": "One person walking their daily route, observing neighbors and taking pride in their community.",
                "weight": 10,
            },
        ],
        "arcs": [
            {
                "name": "Spontaneous Community Help",
                "arc": "Sudden mishap on the street (spilled load, dead battery) -> strangers step in -> problem solved with smiles",
                "ending_flavor": "Heartwarming reminder of everyday human goodness and community solidarity.",
                "weight": 20,
            },
            {
                "name": "Laughing Off the Grind",
                "arc": "Everything goes wrong during a busy day -> sharing the absurdity with a friend -> finding the humor in it",
                "ending_flavor": "Resilience through laughter; the struggle remains but spirits stay high.",
                "weight": 20,
            },
            {
                "name": "The Honest Return",
                "arc": "Finding someone's dropped wallet or phone on transit -> tracking them down -> simple honest gratitude",
                "ending_flavor": "Quiet integrity rewarded with a sincere handshake and restored faith in people.",
                "weight": 16,
            },
            {
                "name": "Standing Up for the Block",
                "arc": "Unfair customer or landlord complaint -> neighbors rallying with calm dignity -> mutual respect established",
                "ending_flavor": "Grounded neighborhood pride and solidarity.",
                "weight": 16,
            },
            {
                "name": "An Unexpected Small Win",
                "arc": "Scraping by on a tight budget -> catching an unexpected break or fair deal -> sharing the relief",
                "ending_flavor": "Honest satisfaction in everyday progress earned through hard work.",
                "weight": 14,
            },
            {
                "name": "Generational Neighborhood Pride",
                "arc": "Changing neighborhood landscape -> old-timer and newcomer sharing stories -> finding common appreciation",
                "ending_flavor": "Continuity and warmth as the neighborhood evolves.",
                "weight": 14,
            },
        ],
        "story_settings_examples": [
            "Neighborhood diner counter or auto repair waiting room on a sunny Saturday morning",
            "Subway platform or crowded bus stop during the 5:30 PM evening commute",
            "Corner grocery store, barbershop, or street fruit market where locals chat",
            "Apartment front stoop or community block cleanup on a warm Sunday afternoon",
            "Crowded subway car during a sudden track delay, strangers commiserating with humor",
            "Auto repair shop waiting area bonding over repair estimates and old cars",
            "Bustling neighborhood flea market on a crisp morning, bargaining for vintage items",
            "Small barbershop where regulars debate sports, neighborhood news, and life",
            "Food truck line on a busy weekend corner, soaking up street energy",
            "Apartment building mailroom sorting out misdelivered packages with neighbors",
            "Community center basketball court at dusk, shooting hoops to unwind from work",
            "24-hour convenience store aisle late at night, chatting with the familiar cashier",
            "Street corner bakery in the morning, greeting neighbors while fresh bread aroma fills the air",
            "Rainy crosswalk under umbrellas, darting through puddles with friendly nods",
            "Hardware store yard picking up lumber and concrete mix with a coworker",
        ],
        "story_conflict_archetypes": [
            "An unexpected car breakdown, missed bus, or lost keys sparking cooperative problem-solving",
            "Navigating rent pressure, tight budgets, and honest everyday hustle with warmth and humor",
            "A spontaneous act of neighborhood kindness turning a stressful day around",
            "Two commuters defusing a tense rush-hour misunderstanding over a seat or spilled coffee with humor",
            "Neighbors organizing together to fix a broken streetlight, pothole, or park bench",
            "A worker balancing double shifts and exhausting commutes while staying hopeful",
            "Standing up for a regular street vendor or immigrant shopkeeper against an unreasonable complaint",
            "Returning a lost wallet or valuable phone found on a bus seat, experiencing everyday integrity",
            "Helping an elderly neighbor carry heavy shopping bags up three flights of stairs",
            "Dealing with an unexpected rent hike or landlord notice by pooling neighborhood advice",
        ],
        "domain_directive": (
            "Use authentic everyday colloquial American English. Keep situations energetic, grounded, and relatable, with zero explicit profanity. "
            "Highlight the genuine warmth, humor, and grit of ordinary urban and neighborhood life. "
            "CREATIVE EXPANSION: Explore bustling morning markets, crowded rush hour commutes, sunny garage sales, and lively barbershops. "
            "INVENT, DO NOT COPY: The setting and conflict examples are structural springboards, never a fixed menu to copy mechanically."
        ),
    },
    "Law, Politics & Society": {
        "setting": "town hall, courtroom, election night, community meeting, news conversation",
        "register": FIELD + ". Keep any sensitive topic factual and non-graphic",
        "default_story": "A grounded story at a community meeting, courtroom, or civic event where real people debate or decide.",
        "critic_name": "🏛️ Civic & Law Critic",
        "props": [
            "a legal petition clipboard with hundreds of handwritten signatures",
            "a case file folder with color-coded index tabs and highlighter marks",
            "a microphone stand on stone courthouse steps with a wind-screen cap",
            "a glass water pitcher and glasses on a municipal council table",
            "a carton of printed campaign flyers with glossy folded edges",
            "a sealed official election ballot envelope with postal stamps",
            "a clear plastic evidence pouch holding water quality sample vials",
            "a yellow legal pad filled with chronological hearing notes and cross-examinations",
            "a green desk lamp shining down on leather-bound civic code volumes",
            "a folded tenant rights notice inside an overcoat pocket",
            "a battery megaphone resting on a folding chair at a civic rally",
            "a brass courthouse visitor security pass on a clip",
            "a newspaper front-page draft with editorial red-pen corrections",
            "an architect's zoning map with colored municipal boundary lines",
        ],
        "times": [
            "8:30 AM courthouse corridors before the morning docket is called",
            "11:00 AM tense town hall hearing, citizen microphones open for public testimony",
            "2:15 PM closed-door mediation room, opposing counsels trading draft compromise terms",
            "5:30 PM city hall steps as an emotional press briefing concludes under camera flashes",
            "8:00 PM grassroots community meeting in a community center basement, folding chairs",
            "11:45 PM legislative committee room, debating final budget amendment text",
            "Dawn rally assembly, unfolding banners as morning mist clears over the square",
        ],
        "character_setups": [
            {
                "type": "advocate_citizen",
                "label": "A legal advocate and an everyday citizen facing a hearing",
                "instruction": "An attorney or advocate prepares a nervous client, reassuring them and planning testimony with calm resolve.",
                "weight": 40,
            },
            {
                "type": "rival_negotiators",
                "label": "Two committee members with opposing views finding common ground",
                "instruction": "Political or ideological rivals putting talking points aside to craft a realistic, fair compromise.",
                "weight": 20,
            },
            {
                "type": "investigative_team",
                "label": "An investigative journalist and editor verifying a major lead",
                "instruction": "Weighing the legal and ethical risks of publishing a sensitive public interest story.",
                "weight": 15,
            },
            {
                "type": "grassroots_coalition",
                "label": "Community organizers planning a neighborhood campaign",
                "instruction": "Neighbors coordinating volunteer shifts, petition drives, and community outreach.",
                "weight": 15,
            },
            {
                "type": "whistleblower_confidant",
                "label": "An insider consulting a trusted friend before speaking out",
                "instruction": "Weighing the personal cost of exposing wrongdoing against the moral duty to the public.",
                "weight": 10,
            },
        ],
        "arcs": [
            {
                "name": "Principled Stand",
                "arc": "Intense institutional pressure -> refusing to compromise on human dignity -> standing firm together",
                "ending_flavor": "Courage in the face of daunting odds; the fight continues with moral clarity.",
                "weight": 20,
            },
            {
                "name": "Hard-Won Compromise",
                "arc": "Deep ideological deadlock -> listening to each other's underlying human concerns -> a pragmatic pact",
                "ending_flavor": "Neither gets everything, but both protect what truly matters for real people.",
                "weight": 20,
            },
            {
                "name": "The Critical Discovery",
                "arc": "Digging through public records -> finding the verifiable document that proves the truth -> presenting proof",
                "ending_flavor": "The quiet triumph of facts, documentation, and persistent investigation.",
                "weight": 18,
            },
            {
                "name": "Protecting the Vulnerable",
                "arc": "Threat of eviction or unfair policy -> organizing legal and community support -> halting the injustice",
                "ending_flavor": "Immediate, tangible relief for working families and neighbors.",
                "weight": 16,
            },
            {
                "name": "Moral Crossroads of Conscience",
                "arc": "Safe silence vs. risky truth -> deciding that silence is complicity -> taking the stand",
                "ending_flavor": "Dignified peace of mind knowing one stood on the right side of history.",
                "weight": 14,
            },
            {
                "name": "Rebuilding Civic Trust",
                "arc": "A community fractured by a bitter debate -> open forum with transparent dialogue -> healing the rift",
                "ending_flavor": "Restored neighborly respect and collective commitment to move forward.",
                "weight": 12,
            },
        ],
        "story_settings_examples": [
            "Courthouse corridor or legal clinic consultation room preparing for a crucial hearing",
            "Town hall or municipal council auditorium during a public debate over local resources",
            "Community organizing office or union hall counting petition signatures late at night",
            "Neighborhood assembly debating a local zoning, environment, or public safety ordinance",
            "Investigative newspaper bullpen or editing suite verifying a major public corruption lead",
            "Public library meeting room where tenant advocates draft a fair housing policy proposal",
            "Legislative anteroom where two opposing lawmakers negotiate bill amendment language",
            "Legal aid clinic desk where a public defender prepares a client for a bail hearing",
            "High school auditorium during an impassioned school board meeting over educational funding",
            "Campaign headquarters on election eve, checking poll registers and volunteer shifts",
            "Civic square or public park rally, advocates holding banners and coordinating speeches",
            "Mediation conference room where two feuding neighborhood associations negotiate a settlement",
            "Environmental advocacy office reviewing water quality test reports to hold polluters accountable",
            "Courthouse steps facing cameras and reporters after a landmark legal verdict",
            "Town clerk archives, researchers examining historical land deeds to resolve a public easement",
        ],
        "story_conflict_archetypes": [
            "A legal advocate and an ordinary citizen standing firm against an unjust policy",
            "Neighbors with opposing political opinions finding common ground on a shared community challenge",
            "Uncovering vital public records or testimony that shifts the entire debate before a final vote",
            "An investigative reporter protecting a vulnerable source while facing intense legal pressure",
            "A young lawyer wrestling between corporate firm ambition and dedication to public interest cases",
            "Balancing passionate civic disagreement with civil discourse, mutual dignity, and safety",
            "A tenant union negotiating with a property management company to prevent wrongful evictions",
            "A small-town mayor listening to skeptical townspeople about a contentious infrastructure project",
            "A whistleblower deciding whether the personal risk of exposure is justified by public safety",
            "Rebuilding trust in a fractured community organization after a contentious leadership election",
        ],
        "domain_directive": (
            "Use articulate civic and spoken conversational English. Keep sensitive topics factual and grounded in everyday human rights, community responsibility, and fair process. "
            "Frame debates around tangible human impacts (homes, schools, clean water, fair treatment) rather than dry legalese. "
            "CREATIVE EXPANSION: Explore sunny courthouse steps, bustling campaign offices, library conference rooms, and neighborhood town halls. "
            "INVENT, DO NOT COPY: The setting and conflict examples are structural springboards, never a fixed menu to copy mechanically."
        ),
    },
    "Business & Career": {
        "setting": "office, meeting, interview, negotiation, first day at work",
        "register": FIELD,
        "default_story": "A realistic story in a workplace where people handle work challenges and relationships.",
        "critic_name": "💼 Business Critic",
        "props": [
            "a slim laptop displaying quarterly forecast spreadsheets, cursor blinking",
            "a handheld slide clicker and whiteboard markers on a conference rail",
            "a commercial espresso portafilter knocking out grounds during the morning rush",
            "a heavy inventory clipboard on a warehouse dock with freight manifests",
            "a bound client proposal folder with embossed company logos",
            "a commercial kitchen ticket rail with orders ticking during the dinner rush",
            "a signed supplier contract folder with blue ink still drying",
            "an ID card and lanyard hung over a desk lamp after hours",
            "a product prototype securely resting in a custom foam casing on a table",
            "a set of marked-up architectural blueprints on a construction trailer desk",
            "a thermal barcode label printer humming as cartons are scanned",
            "a glass carafe of cold brew and ceramic cups on a boardroom table",
            "a sample fabric swatch ring or materials palette spread on a design desk",
            "a business card holder and notebook with action items circled in pen",
        ],
        "times": [
            "7:30 AM early breakfast meeting at a quiet hotel lounge reviewing presentation slides",
            "10:00 AM high-stakes pitch meeting with executive leadership or clients",
            "1:15 PM lunch hour debrief over takeout, discussing tough client feedback",
            "4:30 PM trade show convention floor, networking and closing distribution deals",
            "6:45 PM quiet open-plan office, packing up a laptop after closing a major contract",
            "9:30 PM small business warehouse floor, co-founders packing the first product orders",
            "Midnight quarterly accounting review, finalizing balance sheets before tax deadlines",
        ],
        "character_setups": [
            {
                "type": "duo_colleagues",
                "label": "Two coworkers troubleshooting an urgent operational challenge",
                "instruction": "Two professionals pooling skills to resolve a supply hitch, client deadline, or tactical mistake.",
                "weight": 40,
            },
            {
                "type": "mentor_protege",
                "label": "Seasoned manager and a promising newer team member",
                "instruction": "A constructive, supportive exchange offering career wisdom and honest performance feedback.",
                "weight": 20,
            },
            {
                "type": "co_founders",
                "label": "Two business partners balancing cash flow, risk, and vision",
                "instruction": "Candid discussions between partners making tough strategic decisions about company survival.",
                "weight": 15,
            },
            {
                "type": "negotiating_partners",
                "label": "Two professionals across the negotiation table",
                "instruction": "Firm, respectful bargaining over terms, timelines, and deliverables to reach a win-win.",
                "weight": 15,
            },
            {
                "type": "solo_professional",
                "label": "A professional reflecting on taking the entrepreneurial leap",
                "instruction": "One person wrestling with leaving a comfortable corporate position to build their own business.",
                "weight": 10,
            },
        ],
        "arcs": [
            {
                "name": "Winning with Candor",
                "arc": "Skeptical client or boss -> presenting candid data rather than empty hype -> earning trust and the deal",
                "ending_flavor": "Integrity and hard facts prevail over slick sales pitches.",
                "weight": 20,
            },
            {
                "name": "Standing by Quality",
                "arc": "Intense pressure to cut corners -> defending craft standards and team reputation -> delivering excellence",
                "ending_flavor": "Pride in doing the job right, earning longtime customer respect.",
                "weight": 20,
            },
            {
                "name": "The Tactical Pivot",
                "arc": "Initial strategy encounters a road block -> adapting quickly to market reality -> finding a better path",
                "ending_flavor": "Flexibility and teamwork turn a looming setback into a competitive edge.",
                "weight": 18,
            },
            {
                "name": "Advocating for the Crew",
                "arc": "Leadership overlooks frontline effort -> manager presents operational proof -> securing fair recognition and pay",
                "ending_flavor": "Loyalty to the team validated through concrete leadership action.",
                "weight": 16,
            },
            {
                "name": "Adjusting to Promotion",
                "arc": "Peer becomes supervisor -> navigating the awkward shift in authority -> establishing healthy mutual respect",
                "ending_flavor": "Friendship evolves into professional partnership without resentment.",
                "weight": 14,
            },
            {
                "name": "The Leap of Faith",
                "arc": "Safe routine vs. entrepreneurial vision -> evaluating the calculated risk -> taking the leap with confidence",
                "ending_flavor": "Excitement and clear-eyed courage entering a bold new career chapter.",
                "weight": 12,
            },
        ],
        "story_settings_examples": [
            "Conference room or executive office closing a high-stakes partnership or contract",
            "Interview room or waiting area before a career-defining job interview or review",
            "Warehouse loading dock or retail stockroom handling an urgent logistics deadline",
            "Office desk in the late afternoon where co-founders review quarterly projections",
            "Restaurant kitchen line during Friday dinner rush, head chef and cook coordinating orders",
            "Creative agency pitch room rehearsing slides ten minutes before the client arrives",
            "Local artisan bakery or coffee roasting workshop balancing hand-crafted quality against costs",
            "Trade show convention booth on day two, networking through sore feet and closing deals",
            "Open-plan office at 6:00 PM, two team members debriefing after a tough client feedback call",
            "Small business shipping floor during the holiday rush, sorting manifest delays",
            "Coffee shop patio where a mentor and young professional discuss career trajectory",
            "Co-working space whiteboard room debating product pricing and go-to-market strategy",
            "Print shop or manufacturing plant floor inspecting first-run production samples",
            "Real estate agency reviewing closing documents and escrow requirements",
            "Hotel front desk or guest services handling a corporate booking crisis with composure",
        ],
        "story_conflict_archetypes": [
            "An employee advocating for their worth and team compensation using operational evidence",
            "Two colleagues resolving a tactical disagreement while maintaining professional respect",
            "A team racing to meet a client milestone after a major vendor default",
            "A department head deciding whether to push for a creative innovation or stick to safe protocols",
            "A founder facing a cash-flow squeeze, figuring out how to retain staff without risking survival",
            "Navigating an awkward transition when a longtime colleague is promoted to lead the team",
            "Pitching a bold redesign to a skeptical, conservative client and winning them over with proof",
            "Handling a high-visibility operational mistake transparently with clients rather than covering it up",
            "Balancing professional drive and demanding targets against personal well-being and family",
            "A junior employee discovering a critical discrepancy in financial forecasts and finding courage to raise it",
        ],
        "domain_directive": (
            "Use conversational workplace English. Target words fit natural professional dialogue, team coordination, negotiation, and career milestones. "
            "Highlight practical workplace dynamics: mentorship, deadlines, budget trade-offs, and mutual respect under pressure. "
            "CREATIVE EXPANSION: Explore bustling kitchen lines, artisan workshops, construction trailers, trade shows, and startup garages. "
            "INVENT, DO NOT COPY: The setting and conflict examples are structural springboards, never a fixed menu to copy mechanically."
        ),
    },
}

def get_category_profile(domain: str) -> dict:
    if domain not in CATEGORY_PROFILES and domain != "All Domains":
        logger.warning("Unknown domain '%s' passed to get_category_profile; falling back to 'Basic / Neutral'.", domain)
    return CATEGORY_PROFILES.get(domain, CATEGORY_PROFILES["Basic / Neutral"])


def sample_domain_creative_sparks(domain: str) -> dict:
    """
    Samples a balanced, cohesive set of creative sparks tailored strictly to the specified domain:
    - 2-3 settings
    - 1-2 conflicts
    - 1 time of day
    - 1 character setup (weighted)
    - 1 narrative arc & ending flavor (weighted)
    - 2-3 authentic sensory props
    """
    profile = get_category_profile(domain)
    settings = profile.get("story_settings_examples", [])
    conflicts = profile.get("story_conflict_archetypes", [])
    props = profile.get("props", [])
    times = profile.get("times", [])
    char_setups = profile.get("character_setups", [])
    arcs = profile.get("arcs", [])

    sampled_settings = random.sample(settings, min(3, len(settings))) if settings else []
    sampled_conflicts = random.sample(conflicts, min(2, len(conflicts))) if conflicts else []
    sampled_props = random.sample(props, min(3, len(props))) if props else []
    sampled_time = random.choice(times) if times else "An authentic time of day matching the scene"

    if char_setups:
        weights = [c.get("weight", 1) for c in char_setups]
        sampled_char = random.choices(char_setups, weights=weights, k=1)[0]
    else:
        sampled_char = {
            "type": "duo_dialogue",
            "label": "Two people in direct conversation",
            "instruction": "Two clearly identified characters talk face to face."
        }

    if arcs:
        weights = [a.get("weight", 1) for a in arcs]
        sampled_arc = random.choices(arcs, weights=weights, k=1)[0]
    else:
        sampled_arc = {
            "name": "Classic Resolution",
            "arc": "Problem -> turning point -> quiet determination",
            "ending_flavor": "Characters find a way forward together."
        }

    return {
        "domain": domain,
        "sampled_settings": sampled_settings,
        "sampled_conflicts": sampled_conflicts,
        "time": sampled_time,
        "character_setup": sampled_char,
        "arc": sampled_arc,
        "props": sampled_props,
    }


# Startup verification to guarantee all UI domains map to a profile
_missing = set(DOMAINS) - set(CATEGORY_PROFILES)
assert not _missing, f"Missing category profiles for DOMAINS: {_missing}"

