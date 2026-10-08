import sys, os
sys.path.insert(0, os.path.abspath("."))

from scripts.lyrics_graph import run_critic_only

test_draft = """[Verse 1]
I am an innocent guy.
My mom knows who I am.
I do not give a damn.
Oh my god, I am sorry.
[Chorus]
Please listen when I speak.
We went through hell this week.
A bunch of people lied."""

target_words = ["innocent", "mom", "damn", "sorry", "listen", "hell", "bunch"]
theme = "Street & Daily Life"
genre = "Cinematic / Ballad"
concept = "Two former close friends meet in a diner to apologize, clear up rumors and save their friendship."

print("=== RUNNING LIVE STRICT CRITIC TEST ===")
res = run_critic_only(
    draft=test_draft,
    target_words=target_words,
    theme=theme,
    genre=genre,
    concept=concept,
    dialect="American English"
)

print(f"Overall Score: {res['overall_score']}%")
print(f"Model Used: {res['model_used']}")
print(f"Time Taken: {res['time_taken']}s")
print(f"Passed: {res['passed_count']} | Polished: {res['warn_count']} | Flagged: {res['flagged_count']}\n")
print(f"{'#':<3} | {'Status':<6} | {'Score':<6} | {'Line':<35} | {'Critique / Reason'}")
print("-" * 90)

for line in res["line_breakdown"]:
    num = line.get("number", 0)
    col = line.get("color", "")
    sc = line.get("score", 0)
    txt = line.get("line", "")
    comm = line.get("comment", "")
    print(f"{num:<3} | {col:<6} | {sc:<5}% | {txt:<35} | {comm}")
