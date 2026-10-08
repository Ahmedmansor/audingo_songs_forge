# Project context for coding agents

Before changing this project, read `MASTER_PROMPT.md` in the repository root, then inspect the current files relevant to the requested task. It describes the product goal, existing features, architecture, data semantics, UI preferences, and known implementation gaps. Keep it current when those contracts change.

The central goal: a learner can memorize **any lyric line** and reuse it as natural, useful real-life English. Keep one coherent story and dialect, short memorable lines, no explicit profanity, and everyday target-word meanings. Never force a word into unnatural language to complete coverage or rhyme.

**Basic / Neutral vocabulary is valid in every category.** It is not thematic drift, and the batch-selection blend setting is not a restriction on words allowed in the lyrics. Judge contextual fit by the actual meaning and situation.

Distinguish intended behavior from existing code: legacy prompts contain conflicts documented in `MASTER_PROMPT.md`. Do not silently copy those conflicts into new features. Preserve user data, drafts, locked-line editing boundaries, and vocabulary counters; flag conflicts clearly when they affect the task.

For Streamlit changes, read `.agents/skills/developing-with-streamlit/SKILL.md` when available. For visual design, also consult `design-system/audingo/MASTER.md` and the locally available UI/UX Pro Max skill. Use the existing semantic theme tokens and verify both dark and light appearances.

Do not run data ingestion, migrations, approval/deletion flows, or tests against the user's production `ngsl_vocab.db` merely to verify a change. Use temporary databases or isolated copies, accounting for database paths bound as default function arguments at import time.
