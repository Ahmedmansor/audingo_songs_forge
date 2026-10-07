"""
db.py — Unified database facade for Audingo Songs Forge.
Re-exports connection, schema, and repositories for backwards compatibility.
"""

from data.database.connection import (
    DB_PATH,
    get_connection,
    get_cairo_now_str,
    init_db,
)

from data.repositories.word_repository import (
    get_all_ngsl_words,
    get_extra_words,
    get_progress_stats,
    get_domain_counts,
    get_domain_detailed_stats,
    get_words_domains,
    compute_domain_breakdown,
    pull_20_words,
    pull_candidate_pool_for_thematic_curation,
    build_curated_batch_from_words,
    swap_single_word,
    get_all_lemma_mappings,
    get_used_ngsl_words,
    get_previously_used_words,
    CORE_EXEMPT_WORDS,
)

from data.repositories.song_repository import (
    approve_and_save_song,
    get_all_songs,
    update_song,
    delete_song,
    migrate_past_songs_bonus_words,
)

from data.repositories.variant_repository import (
    upsert_track_variant,
    save_track_variant,
    get_track_variants,
    get_track_variant_by_combo,
    update_track_variant,
    delete_track_variant,
    upsert_poster_prompt,
    get_poster_prompts,
    update_poster_prompt,
    delete_poster_prompt,
)

from data.repositories.draft_repository import (
    save_active_batch_state,
    load_active_batch_state,
    clear_active_batch_state,
    save_studio_draft,
    list_studio_drafts,
    load_studio_draft,
    delete_studio_draft,
)
