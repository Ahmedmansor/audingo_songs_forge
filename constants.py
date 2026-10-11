"""
constants.py — Fixed lists and configurations for Audingo Songs Forge.
"""

import logging
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
        "story_settings_examples": [
            "Everyday home, neighborhood, or shared social setting",
            "A casual coffee break, walk, or phone call between close friends",
            "A family gathering or roommates handling everyday tasks together",
            "Kitchen table on a Sunday evening planning a weekly budget or sorting through old receipts",
            "Neighborhood driveway or garage on a Saturday morning fixing a sputtering lawnmower or car with a neighbor",
            "Subway platform or delayed commuter train where two travelers or coworkers share an unexpected honest conversation",
            "Hardware store aisle or home workshop trying to figure out the right tools for a DIY weekend repair",
            "Laundromat late at night waiting for the spin cycle while trading stories about work and family",
            "Local park bench, community garden plot, or dog-walking trail meeting a neighbor at dusk",
            "Supermarket checkout line or grocery parking lot dealing with a runaway cart, spilled groceries, or a forgotten wallet",
            "Late-night highway drive or parked at a roadside rest stop, talking through a life-changing decision between two friends",
            "Front porch or apartment balcony at sunset sharing leftover takeout while unwinding after a tough week",
            "Rainy roadside or 24-hour gas station waiting out a sudden summer downpour while grabbing coffee",
            "Quiet hospital or clinic waiting room late at night, whispering comfort while waiting for difficult news",
            "An old diner booth late at night over lukewarm coffee, two friends clearing the air after months of unspoken distance",
            "Empty train station platform or bus depot at dawn, watching taillights pull away after a painful goodbye",
            "Quiet kitchen table at 2 AM with cold tea, sitting with grief or a heavy heart after a relationship ends",
            "A quiet hospital corridor or pharmacy counter, waiting for test results and whispering steady reassurance",
            "Rainy park bench or quiet porch, sitting with an empty chair and speaking memories to someone who is gone",
            "A busy airport departure gate during a long weather delay, two travelers having an unexpectedly candid talk",
            "Standing over the kitchen sink washing dinner dishes together, working through an awkward disagreement with honest apologies",
            "A quiet workplace breakroom between shifts, two colleagues sharing a meal and talking through family pressure",
            "Waiting under a shared umbrella at a windy bus stop in the rain, laughing off a rough day at work",
            "Sitting on front porch steps early on a Sunday morning with hot mugs, talking through doubts about a new job or relationship",
        ],
        "story_conflict_archetypes": [
            "A relatable personal dilemma, decision, or shared moment between friends or family",
            "Overcoming a daily obstacle through mutual support and clear communication",
            "Two friends resolving an awkward miscommunication over loaned money or an unkept promise with honest, clear words",
            "Roommates or partners negotiating domestic chores and personal space without turning it into an argument",
            "A neighbor offering unexpected hands-on help when another is overwhelmed by a sudden household breakdown",
            "Two friends reconciling after a prolonged falling out, putting pride aside to speak the truth",
            "A person wrestling with whether to take a modest life risk (moving, changing routine) and seeking a trusted friend's candid advice",
            "Overcoming unexpected daily frustration (bad weather, flat tire, missed bus) by laughing it off and teaming up to fix it",
            "Processing quiet grief or deep personal loss with honest, comforting words between close loved ones",
            "A painful but unavoidable parting between close friends or family due to distance, illness, or changing life paths",
            "Coming to terms with a shattered dream or heavy disappointment without anger, finding solace in quiet acceptance",
            "Supporting an aging parent or friend through failing health, balancing deep sorrow with gentle tenderness",
            "Dealing with quiet loneliness, homesickness, or regret in an unfamiliar city, reaching out across the miles",
            "Struggling with burnout and feeling trapped in a daily routine, finding courage through a loved one's honest perspective",
            "A parent and grown child at a quiet breakfast diner, bridging a long-standing generational misunderstanding",
            "Two coworkers handling an unexpected blunder before the morning shift starts, backing each other up",
        ],
        "domain_directive": (
            "Use clear, natural spoken English suitable for everyday life. "
            "Prioritize conversational dialogue that any native speaker would say to a friend. "
            "Because these words are universal, foundational everyday terms, integrate them actively into characters' dialogue, questions, and reactions. "
            "FULL EMOTIONAL SPECTRUM (INCLUDING SADNESS & POIGNANCY): Real everyday life encompasses deep sorrow, painful goodbyes, quiet grief, and poignant nostalgia just as much as lighthearted moments. "
            "Do NOT shy away from sad or bittersweet scenarios when the words or mood suggest it; treat sadness as an authentic, profound pillar of everyday human experience. "
            "NO CLICHÉ FIXATIONS (STRICT BAN ON 'PACKING CARDBOARD BOXES' / 'MOVING APARTMENT' / 'ATTIC DECLUTTERING' TROPES): "
            "Real life is NOT a conveyor belt of people sitting on floors packing cardboard boxes! Do NOT repeatedly default to moving boxes, packing up apartments, or sorting attic keepsakes. "
            "Explore the full range of authentic human interactions: cars in traffic, diner booths at 1 AM, hospital waiting rooms, airport gates, bus stops in the rain, breakrooms between shifts, cooking dinner together at the stove, walking down the street at dusk, front steps at night, and late-night phone calls. "
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
        "story_settings_examples": [
            "University research laboratory or science facility working late before a grant or paper submission deadline",
            "Tech startup, IT office, or software engineering team troubleshooting a critical system crash or bug before launch",
            "Engineering workshop, garage, or robotics bench testing an experimental hardware prototype under pressure",
            "Medical clinic, diagnostic lab, or clinical study reviewing complex patient data or trial outcomes",
            "College campus study room or library where graduate students prepare for a high-stakes capstone defense or exam",
            "Field ecology station or oceanographic survey vessel in rough weather, logging critical environmental telemetry",
            "Late-night cybersecurity operations center responding to a sudden network breach alert and isolating server logs",
            "Hospital pathology or radiology suite, two specialists comparing high-resolution scans and debating an ambiguous diagnosis",
            "Architecture studio surrounded by draft models and blueprints, debating structural load versus aesthetic design",
            "Astronomy observatory control room at 3 AM with telemetry monitors humming as rain lashes the copper dome",
            "Pharmaceutical trial review meeting, balancing safety board findings against urgent timeline pressures",
            "University faculty office after hours, a mentor and a graduate student candidly re-evaluating thesis direction",
            "Meteorology tracking desk during an incoming storm, coordinating radar feeds and arguing over evacuation forecasts",
            "Archaeological dig site tent at dusk, cataloging fragile artifacts and discussing their historical significance",
            "Classroom or workshop bench after a failed experiment, an instructor showing an apprentice how to diagnose errors",
        ],
        "story_conflict_archetypes": [
            "Two researchers racing the clock when test results vary wildly hours before their project deadline",
            "A software engineer and team lead debating whether to rewrite core logic or push a quick patch",
            "A specialist and an apprentice discovering an unexpected flaw in their original assumptions and finding a fix",
            "Colleagues pushing through exhaustion, pooling their knowledge, and celebrating a hard-won discovery",
            "Defending unconventional experimental findings before a skeptical academic review panel with calm empirical rigor",
            "A data analyst and project lead clashing over whether user metrics ethically justify changing an algorithm",
            "Field researchers confronting equipment failure in harsh wilderness and relying on manual calculations to succeed",
            "A mentor helping a talented student overcome imposter syndrome before delivering a major conference presentation",
            "Balancing commercial pressure for speed against uncompromising scientific safety standards",
            "A medical team wrestling with whether to publish a negative trial result that disproves their own long-held hypothesis",
        ],
        "domain_directive": (
            "Accept educated, professional spoken English (collegiate, tech, lab, or clinical dialogue); street slang is NOT the standard. "
            "Anchor target words in active spoken dialogue between collaborators (e.g. 'demonstrate the fix', 'we need a specialist', "
            "'the error is constant', 'results vary between tests', 'don't be too critical', 'describe what failed', 'that occupies my time'). "
            "Do NOT drop academic or technical words simply because they sound educated; native speakers use them constantly in these settings. "
            "INVENT, DO NOT COPY: The setting and conflict examples are structural springboards, never a fixed menu to copy mechanically."
        ),
    },
    "Emotions & Relationships": {
        "setting": "a real moment between family, friends, or partners",
        "register": CASUAL,
        "default_story": "A heartfelt story about two people working through a real emotional moment.",
        "critic_name": "❤️ Emotions Critic",
        "story_settings_examples": [
            "Quiet kitchen table or late-night coffee shop where partners talk through an unspoken truth",
            "Airport departure gate, bus depot, or train platform before an extended separation",
            "Long drive at dusk or quiet porch where old friends address a past misunderstanding",
            "Backyard family reunion or quiet bedside conversation during recovery",
            "Sitting on the hood of a car overlooking city lights at midnight, confessing feelings that were hidden for years",
            "Park bench under autumn trees, two estranged friends meeting after years of silence to see if the bond survives",
            "A crowded party or wedding reception, slipping out onto a quiet balcony to share an honest, intimate conversation",
            "A diner booth in the early morning over black coffee, breaking the news of a necessary life decision with gentle honesty",
            "Living room listening to old music late at night, reminiscing about when life felt simpler and more hopeful",
            "Rainy evening waiting in a parked car with wipers running, working through a painful relationship crossroads",
            "Quiet hospital room holding a loved one's hand, whispering memories and offering steady comfort through illness",
            "A long walk through a quiet neighborhood at midnight, finally apologizing for words spoken in anger",
            "Kitchen counter preparing breakfast together on a quiet Sunday, laughing about quirks and reaffirming everyday commitment",
            "A lake shore or beach at dawn, two friends reflecting on how their paths diverged without losing mutual love",
            "A phone call across time zones late at night, dealing with homesickness and longing for someone far away",
        ],
        "story_conflict_archetypes": [
            "Overcoming fear of vulnerability to confess honest feelings and reconcile",
            "Two close friends working through distance and changing life priorities without losing their bond",
            "Reassuring a partner or family member through grief, uncertainty, or personal transition",
            "Swallowing stubborn pride to say 'I'm sorry' and mend an old fracture between siblings or friends",
            "Recognizing that two people have grown apart, choosing mutual respect and kindness over bitter blame",
            "Supporting a partner through sudden career loss or personal crisis without making them feel inadequate",
            "Navigating the delicate line between giving someone space and showing up when they feel deeply lonely",
            "Forgiving an old broken promise and choosing to build trust from scratch with open, honest eyes",
            "Wrestling with whether to confess romantic feelings at the risk of complicating a treasured friendship",
            "Comforting an aging parent who fears becoming a burden, reassuring them of unconditional love and presence",
        ],
        "domain_directive": (
            "Focus on emotionally authentic, heartfelt spoken English. Keep dialogue tender, vulnerable, and grounded in real human connection. "
            "Let emotional weight come from understated, honest conversational lines rather than melodramatic poetry. "
            "INVENT, DO NOT COPY: The setting and conflict examples are structural springboards, never a fixed menu to copy mechanically."
        ),
    },
    "Street & Daily Life": {
        "setting": "streets, neighborhoods, errands, friends hanging out",
        "register": CASUAL,
        "default_story": "A relatable real-life story about people handling daily life and social moments.",
        "critic_name": "🏙️ Street Life Critic",
        "story_settings_examples": [
            "Neighborhood diner counter, auto repair shop, or laundromat on a busy Saturday morning",
            "Subway platform, crowded bus stop, or city sidewalk during the evening rush",
            "Corner grocery store, barber shop, or street market where locals chat and trade news",
            "Apartment stoop or block party where neighbors deal with daily neighborhood drama",
            "A crowded subway car during a sudden track delay, strangers trading wry jokes and commiserating over commutes",
            "An auto repair shop waiting room with the TV on mute, bonding with fellow drivers over mechanic estimates and car troubles",
            "A bustling neighborhood farmer's market or flea market on a crisp Saturday morning, bargaining for vintage items",
            "A small barbershop or hair salon where regulars debate sports, neighborhood news, and life philosophies",
            "Late-night food truck line on a busy weekend corner, soaking up the city energy and chatting with night owls",
            "Apartment building laundry room or mailroom, negotiating parcel deliveries and trading landlord updates with neighbors",
            "A local community center gym or basketball court at dusk, shooting hoops and unwinding from blue-collar workday stress",
            "A 24-hour convenience store neon aisle at 2 AM, grabbing snacks and chatting with the familiar clerk on night shift",
            "Street corner fruit stand or bakery in the morning, greeting neighbors while fresh bread and coffee aroma fill the sidewalk",
            "A rainy crosswalk under bright umbrella canopies, darting through puddles and smiling at fellow commuters",
            "A neighborhood garage sale or block cleanup, working side-by-side with neighbors to spruce up the block",
        ],
        "story_conflict_archetypes": [
            "An unexpected car breakdown, missed bus, or lost keys sparking cooperative problem-solving",
            "Navigating rent pressure, tight budgets, and honest everyday hustle with warmth and humor",
            "A spontaneous act of neighborhood kindness turning a stressful day around",
            "Two commuters defusing a tense rush-hour misunderstanding over a seat or spilled coffee with humor and patience",
            "Neighbors organizing together to fix a broken streetlight, pothole, or park bench when city services are delayed",
            "A worker balancing double shifts and exhausting commutes while staying hopeful and supporting a young family",
            "Standing up for a regular street vendor or immigrant shopkeeper against an unreasonable customer complaint",
            "Returning a lost wallet or valuable phone found on a bus seat, experiencing the simple integrity of honest people",
            "Helping an elderly neighbor carry heavy shopping bags up three flights of stairs in a walk-up building",
            "Dealing with an unexpected rent hike or landlord notice by pooling neighborhood advice and practical resources",
        ],
        "domain_directive": (
            "Use authentic everyday colloquial American English. Keep situations energetic, grounded, and relatable, with zero explicit profanity. "
            "Highlight the genuine warmth, humor, and grit of ordinary urban and neighborhood life. "
            "INVENT, DO NOT COPY: The setting and conflict examples are structural springboards, never a fixed menu to copy mechanically."
        ),
    },
    "Law, Politics & Society": {
        "setting": "town hall, courtroom, election night, community meeting, news conversation",
        "register": FIELD + ". Keep any sensitive topic factual and non-graphic",
        "default_story": "A grounded story at a community meeting, courtroom, or civic event where real people debate or decide.",
        "critic_name": "🏛️ Civic & Law Critic",
        "story_settings_examples": [
            "Courthouse corridor, legal clinic, or consultation room preparing for a crucial hearing",
            "Town hall, municipal council room, or school auditorium during a heated public forum",
            "Community center or grassroots organizing office counting petition signatures late at night",
            "Neighborhood assembly debating a local zoning, environment, or public safety resolution",
            "Investigative newspaper bullpen or broadcast news editing suite racing to verify a major public corruption lead before printing",
            "Public library conference room where tenant advocates and community leaders draft a fair housing proposal",
            "State legislature or city council anteroom, two opposing lawmakers negotiating amendment language late at night",
            "Legal aid clinic desk where an overworked public defender prepares a client for a high-stakes bail hearing",
            "High school auditorium during an impassioned school board election debate over educational funding and curriculum",
            "Grassroots campaign phone bank or volunteer headquarters on election eve, checking poll registers and volunteer shifts",
            "Public park rally or peaceful civic march, advocates holding banners and coordinating speeches through megaphones",
            "A mediation room where two feuding neighborhood associations negotiate a shared commercial easement agreement",
            "Environmental advocacy field office reviewing water quality test reports to hold a negligent manufacturer accountable",
            "Courthouse steps facing cameras and reporters, an attorney and plaintiff delivering an honest statement after a landmark verdict",
            "Civic archives or town clerk office, researchers digging through historical property deeds to resolve a disputed public easement",
        ],
        "story_conflict_archetypes": [
            "A legal advocate and an ordinary citizen standing firm against an unjust policy",
            "Neighbors with opposing political opinions finding common ground on a shared community challenge",
            "Uncovering vital public records or testimony that shifts the entire debate before a final vote",
            "An investigative reporter protecting a vulnerable source while facing intense editorial and legal pressure to reveal names",
            "A young lawyer wrestling between corporate firm career ambition and dedication to pro-bono public interest cases",
            "Balancing free speech and passionate civic disagreement with civil discourse, mutual dignity, and safety",
            "A tenant union negotiating with an aggressive property management company to prevent wrongful winter evictions",
            "A small-town mayor listening to skeptical townspeople about a contentious new infrastructure tax or highway project",
            "A whistleblower deciding whether the personal risk of exposure is justified by the moral duty to protect public safety",
            "Rebuilding trust in a fractured community organization after a contentious leadership election",
        ],
        "domain_directive": (
            "Use articulate civic and spoken conversational English. Keep sensitive topics factual and grounded in everyday human rights, community responsibility, and fair process. "
            "Frame debates around tangible human impacts (homes, schools, clean water, fair treatment) rather than dry legalese. "
            "INVENT, DO NOT COPY: The setting and conflict examples are structural springboards, never a fixed menu to copy mechanically."
        ),
    },
    "Business & Career": {
        "setting": "office, meeting, interview, negotiation, first day at work",
        "register": FIELD,
        "default_story": "A realistic story in a workplace where people handle work challenges and relationships.",
        "critic_name": "💼 Business Critic",
        "story_settings_examples": [
            "Glass conference room or executive office closing a high-stakes partnership or contract",
            "Waiting area or interview room before a career-defining job interview or performance review",
            "Busy warehouse, restaurant floor, or retail stockroom handling an urgent supply deadline",
            "Late-night office desk where co-founders balance financial reality with company vision",
            "A bustling restaurant kitchen line during the Friday dinner rush, the head chef and line cook coordinating ticket orders",
            "A creative design agency pitch room rehearsing slides and client talking points ten minutes before the presentation",
            "A local artisan bakery or coffee roasting workshop balancing hand-crafted quality against rising supplier overhead",
            "Trade show convention booth on day three, networking through sore feet and closing crucial distribution deals",
            "A corporate open-plan office at 6 PM, two team members debriefing after a tough client feedback call",
            "A small business stockroom or logistics loading dock during the holiday rush, sorting manifest delays and freight tracking",
            "A quiet coffee shop patio where a mentor and young professional discuss quitting a secure job to start a new venture",
            "A modern co-working space brainstorming whiteboard, debating product pricing models and go-to-market strategies",
            "A manufacturing plant floor or print shop inspecting first-batch production samples and checking quality tolerances",
            "A real estate agency office reviewing closing documents and negotiating counter-offers on an escrow deadline",
            "A hotel front desk or customer relations office handling an escalated corporate booking crisis with poise and diplomacy",
        ],
        "story_conflict_archetypes": [
            "An employee advocating for their worth and team compensation using clear operational evidence",
            "Two colleagues resolving a tactical disagreement while maintaining mutual professional respect",
            "A team racing to meet a client milestone after a major vendor default",
            "A department head deciding whether to push for a risky creative innovation or play it safe with established protocols",
            "A founder facing a cash-flow squeeze, figuring out how to retain loyal staff without compromising company survival",
            "Navigating an awkward transition when a longtime colleague is promoted to become the team's new supervisor",
            "Pitching a radical redesign to a skeptical, conservative client and winning them over with demonstrable data",
            "Handling a high-visibility operational mistake transparently with clients rather than covering it up",
            "Balancing intense professional drive and demanding quarterly targets against personal well-being and family time",
            "A junior employee discovering a critical discrepancy in financial forecasts and finding the courage to raise it to senior leadership",
        ],
        "domain_directive": (
            "Use conversational workplace English. Target words fit natural professional dialogue, team coordination, negotiation, and career milestones. "
            "Highlight practical workplace dynamics: mentorship, deadlines, budget trade-offs, and mutual respect under pressure. "
            "INVENT, DO NOT COPY: The setting and conflict examples are structural springboards, never a fixed menu to copy mechanically."
        ),
    },
}

def get_category_profile(domain: str) -> dict:
    if domain not in CATEGORY_PROFILES and domain != "All Domains":
        logger.warning("Unknown domain '%s' passed to get_category_profile; falling back to 'Basic / Neutral'.", domain)
    return CATEGORY_PROFILES.get(domain, CATEGORY_PROFILES["Basic / Neutral"])

# Startup verification to guarantee all UI domains map to a profile
_missing = set(DOMAINS) - set(CATEGORY_PROFILES)
assert not _missing, f"Missing category profiles for DOMAINS: {_missing}"
