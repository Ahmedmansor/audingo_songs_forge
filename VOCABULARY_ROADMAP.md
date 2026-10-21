# Remaining Vocabulary Roadmap — Audingo Songs Forge

Updated October 21, 2026. This replaces the earlier 715-word / fixed 6–7 modifier plan.

## Inventory snapshot

At the read-only review: 2,135 of 2,809 NGSL headwords covered (76%), 674 remaining.
Counts change after song approval; always use live inventory for the next pull.

| Domain | Nouns | Verb bucket | Other, non-exempt | Other, exempt | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Basic / Neutral | 0 | 129 | 51 | 7 | 187 |
| Emotions & Relationships | 0 | 120 | 13 | 3 | 136 |
| Science, Tech & Academia | 35 | 97 | 58 | 4 | 194 |
| Law, Politics & Society | 43 | 40 | 0 | 0 | 83 |
| Street & Daily Life | 10 | 21 | 13 | 3 | 47 |
| Business & Career | 12 | 15 | 0 | 0 | 27 |
| Total | 100 | 422 | 135 | 17 | 674 |

No unused adjective-bucket entries remain in this snapshot. POS buckets are imperfect selection metadata:
words in the verb bucket can have ordinary noun/adjective uses; Other includes prepositions and connectors.
Never force a rare meaning or grammatical use to match a bucket.

## Current phase: Emotions + Basic

Keep Emotions & Relationships selected and Blend Joker enabled. Draw targets only from these two sources.
The 313 non-exempt candidates contain 249 verb-bucket words and 64 modifiers/connectors.
For a 20-word batch, round `20 * 64 / 313` to 4 modifiers, with 16 verb-bucket words.

| Source | Verb bucket | Modifiers/connectors | Total |
| --- | ---: | ---: | ---: |
| Emotions | 9 | 1 | 10 |
| Basic / Neutral | 7 | 3 | 10 |

This is an inventory-derived starting point, not a permanent quota. Recompute after approvals.
If nouns return to the eligible inventory, allocate available nouns first, then balance remaining slots.
If one source runs short, compensate only from the other authorized source.
Smart curation receives source/POS constraints; the final batch enforces them and contains unique words.
Basic alone stays Basic; disabling blending stays in the selected domain; All Domains permits all sources.
Single/multiple replacements do not fall through to unrelated domains when a category is selected.

Review actual newly covered words after every three approved songs. Repeatedly dropped words need a better
situation, not forced lyrics. The 313 candidates require at least 16 fully successful 20-word batches without
bonus coverage; actual songs depend on dropped targets, bonus words and the source split. No fixed promise
of clearing Basic in 10–14 songs. Exempt words are separate and should not be assumed automatically credited.

## Subsequent phases

Continue with smaller domains (Business, Street), then Law and Science as desired. Recompute source and POS
availability at each step; Basic remains valid support in every category. Its use in lyrics is always allowed,
even after no unused Basic targets remain. Do not assume exactly 20 candidates exist near the end.

## Dynamic stories for every domain and pull path

Random batch -> mood/story analysis and Smart Thematic Pull share `domain/services/story_policy.py`.
Keep each story in its domain, choose a human event from the words, and make time, objects and scenery optional.
No stock opening, beverage, emotional trajectory, compulsory tragedy or compulsory happy ending.
Recent saved concepts (last 12 in the same source domain; all domains for All Domains) guide novelty in
relationship, trigger, conflict and ending. Unsaved rerolls are not included. Existing user concepts are preserved.
Lyric drafting preserves the chosen emotional stakes and ending. Prompt instructions guide an LLM; they do not
prove story quality or guarantee unique output. Natural reusable English, coherence and clean language take priority.
