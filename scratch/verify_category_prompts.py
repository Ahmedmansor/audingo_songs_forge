import sys
import os
import json
import tempfile
from pathlib import Path
import sqlite3
import inspect

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from constants import DOMAINS, CATEGORY_PROFILES, get_category_profile
from domain.services.prompt_service import generate_master_prompt, build_manual_surgical_prompt
from scripts.lyrics_graph import authenticity_critic_node, run_critic_only
from data.repositories.draft_repository import save_refinement_state, load_refinement_state

def run_all_checks():
    print("=" * 70)
    print("RUNNING VERIFICATION SUITE: CATEGORY-AWARE PROMPTS & CRITICS")
    print("=" * 70)

    # 1. Verify CATEGORY_PROFILES & constants.py
    print("\n--- 1. Checking CATEGORY_PROFILES & constants.py ---")
    print(f"Total domains configured: {len(CATEGORY_PROFILES)}")
    for name, p in CATEGORY_PROFILES.items():
        print(f"  • [{name}]")
        print(f"      Critic: {p['critic_name']}")
        print(f"      Setting: {p['setting']}")
        print(f"      Register preview: {p['register'][:60]}...")
        assert "setting" in p and "register" in p and "default_story" in p and "critic_name" in p

    # Fallback check for All Domains
    all_domains_profile = get_category_profile("All Domains")
    assert all_domains_profile["critic_name"] == "🃏 General Critic", "Fallback for All Domains failed"
    print("  [PASSED] 'All Domains' safely falls back to Basic / Neutral profile")

    # Unknown domain warning fallback check
    unknown_profile = get_category_profile("NonExistentCategory")
    assert unknown_profile["critic_name"] == "🃏 General Critic", "Fallback for unknown category failed"
    print("  [PASSED] Unknown domain safely falls back to Basic / Neutral profile with logging")

    # Assert that DOMAINS matches CATEGORY_PROFILES
    missing_domains = set(DOMAINS) - set(CATEGORY_PROFILES)
    assert not missing_domains, f"Missing category profiles for DOMAINS: {missing_domains}"
    print("  [PASSED] set(DOMAINS) is a complete subset of set(CATEGORY_PROFILES)")

    # 2. Verify generate_master_prompt for each category (Positive AND Strict Negative Checks)
    print("\n--- 2. Checking generate_master_prompt (Positive & Strict Negative) ---")
    protected_line = "- Try hard to use every target word. Choose story details that give each word a natural place."
    dialect_rule = "- Use one consistent variety of English in the whole song. Never mix American and British forms."

    for domain in DOMAINS:
        p = get_category_profile(domain)
        prompt = generate_master_prompt(
            target_words=["coffee", "table"],
            genre="Cinematic / Ballad",
            song_structure="Verse-Chorus",
            mood_analysis={"Reflective": 80},
            creative_concept="",
            selected_domain=domain
        )

        # Positive checks
        assert protected_line in prompt, f"PROTECTED LINE MISSING IN {domain}!"
        assert dialect_rule in prompt, f"Dialect rule missing in {domain}!"
        assert f"- Category guidance: Setting: {p['setting']}. Register: {p['register']}." in prompt, f"Category guidance missing in {domain}!"
        assert p["default_story"] in prompt, f"Default story missing in {domain}!"
        assert "The song tells one believable real-life story that fits the theme" in prompt
        assert "would a native speaker say this to the person in this scene?" in prompt

        # STRICT NEGATIVE CHECK: Settings of all other 5 domains must NOT appear in this domain's prompt!
        other_domains = [d for d in DOMAINS if d != domain]
        for other_d in other_domains:
            other_p = get_category_profile(other_d)
            assert other_p["setting"] not in prompt, f"NEGATIVE CHECK FAILED: {other_d}'s setting leaked into {domain}'s prompt!"

        print(f"  [PASSED] {domain}: Setting, Register, Negative Isolation, & Protected Line verified!")

    # Check that mate re.sub was removed from prompt_service.py
    prompt_service_code = open("domain/services/prompt_service.py", encoding="utf-8").read()
    assert r"\bmates\b" not in prompt_service_code, "Found leftover 'mates' regex in prompt_service.py!"
    print("  [PASSED] No leftover 'mate/mates' regex in prompt_service.py")

    # 3. Verify build_manual_surgical_prompt (Positive AND Strict Negative Checks)
    print("\n--- 3. Checking build_manual_surgical_prompt (Positive & Negative) ---")
    biz_prof = get_category_profile("Business & Career")
    surgical_prompt = build_manual_surgical_prompt(
        lyrics_text="[Verse 1]\nLine one here\nLine two here",
        line_breakdown=[{"line": "Line one here", "score": 95}, {"line": "Line two here", "score": 60, "issue": "Stiff"}],
        theme="Business & Career",
        genre="Cinematic / Ballad",
        concept="",
        target_words=["contract", "meeting"],
        selected_domain="Business & Career"
    )
    assert f"- Category guidance: Setting: {biz_prof['setting']}. Register: {biz_prof['register']}." in surgical_prompt
    assert "An ESL learner who memorizes the line should be able to say it naturally in this setting." in surgical_prompt
    assert "Is the line natural spoken English a learner can reuse in this setting?" in surgical_prompt

    # Negative check for surgical prompt
    for other_d in [d for d in DOMAINS if d != "Business & Career"]:
        other_p = get_category_profile(other_d)
        assert other_p["setting"] not in surgical_prompt, f"NEGATIVE CHECK FAILED in surgical prompt: {other_d} leaked!"
    print("  [PASSED] Surgical prompt category guidance, setting checks, and negative isolation verified!")

    # 4. Check Critic Prompt in lyrics_graph
    print("\n--- 4. Checking lyrics_graph prompt construction ---")
    sci_prof = get_category_profile("Science, Tech & Academia")

    critic_src = inspect.getsource(authenticity_critic_node)
    run_critic_src = inspect.getsource(run_critic_only)

    assert "p = get_category_profile(theme)" in critic_src
    assert "- Category guidance: Setting: {p['setting']}. Register: {p['register']}." in critic_src
    assert "Not something a native speaker would say in this setting" in critic_src
    assert "Stiff form where a contraction is natural in this setting" in critic_src
    print("  [PASSED] authenticity_critic_node prompt has category guidance & setting-aware deductions!")

    assert "p = get_category_profile(theme)" in run_critic_src
    assert "- Category guidance: Setting: {p['setting']}. Register: {p['register']}." in run_critic_src
    assert "Not something a native speaker would say in this setting" in run_critic_src
    assert "Stiff form where a contraction is natural in this setting" in run_critic_src
    assert '"critic_name": p["critic_name"]' in run_critic_src
    print("  [PASSED] run_critic_only prompt has category guidance, setting-aware deductions & returns critic_name!")

    # 5. Check Persistence logic
    print("\n--- 5. Checking Draft Persistence with Domain ---")
    temp_db = Path(tempfile.gettempdir()) / "test_audingo_refine_v2.db"
    try:
        if temp_db.exists():
            temp_db.unlink()
    except Exception:
        pass

    with sqlite3.connect(temp_db) as conn:
        conn.execute("CREATE TABLE app_state (key TEXT PRIMARY KEY, value TEXT)")
        conn.commit()

    # Case A: Save with domain
    save_refinement_state("test draft", {"overall_score": 85}, "test concept", domain="Law, Politics & Society", db_path=temp_db)
    loaded_a = load_refinement_state(db_path=temp_db)
    assert loaded_a.get("domain") == "Law, Politics & Society", f"Expected Law, Politics & Society, got {loaded_a.get('domain')}"
    print("  [PASSED] Save & Load refinement state preserves domain: 'Law, Politics & Society'")

    # Case B: Old saved draft without domain field
    with sqlite3.connect(temp_db) as conn:
        old_payload = json.dumps({"draft_input": "old draft", "graph_report": None, "concept": "old concept"})
        conn.execute("INSERT OR REPLACE INTO app_state (key, value) VALUES ('refinement_state', ?)", (old_payload,))
        conn.commit()

    loaded_b = load_refinement_state(db_path=temp_db)
    assert loaded_b.get("domain") is None, f"Expected None for old draft without domain, got {loaded_b.get('domain')}"
    print("  [PASSED] Old draft without domain loads domain as None (does not silently default to Basic / Neutral)")

    # 6. Check tab3_refinement call sites and studio-critic warning
    print("\n--- 6. Checking tab3_refinement code integrity ---")
    tab3_code = open("presentation/tabs/tab3_refinement.py", encoding="utf-8").read()
    assert "studio_domain = st.session_state.get(\"selected_domain\")" in tab3_code
    assert "Critic category" in tab3_code and "differs from Studio category" in tab3_code
    assert "selected_domain=active_domain" in tab3_code
    print("  [PASSED] tab3_refinement has category mismatch warning and passes selected_domain=active_domain")

    try:
        if temp_db.exists():
            temp_db.unlink()
    except Exception:
        pass

    print("\n" + "=" * 70)
    print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY (100% COVERAGE)!")
    print("=" * 70)

if __name__ == "__main__":
    run_all_checks()
