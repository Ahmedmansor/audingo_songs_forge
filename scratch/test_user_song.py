import sys, os, time
sys.path.insert(0, os.path.abspath("."))

from scripts.lyrics_graph import run_critic_only

user_input = """[Title]: Two Cups, One Last Chance
[Genre]: Cinematic / Ballad
[Suno Style]: Cinematic ballad, steady 110 bpm, clear upfront male vocals, emotive grand piano, lush strings, soft intimate verses, building dynamics, powerful chorus, clean dynamic mix

[Lyrics]:
[Verse 1]
It's late and the diner's quiet.
A lady brings us two coffees.
You haven't looked me in the eye.
I know you're still mad about last night.

[Pre-Chorus]
Please listen to me for one minute.
I never said those things about you.
Now a bunch of people think I did.
But I'm innocent, I swear to God.

[Chorus]
Just be honest with me tonight.
I'm sorry, I made a mistake.
I'm not mad at you anymore.
Let's not throw our friendship away.

[Verse 2]
Yesterday my mom called me crying.
She asked me why you don't call.
I've been through hell this whole week.
It's killing me to lose you at all.

[Pre-Chorus]
Please listen to me for one minute.
I never said those things about you.
Now a bunch of people think I did.
But I'm innocent, I swear to God.

[Chorus]
Just be honest with me tonight.
I'm sorry, I made a mistake.
I'm not mad at you anymore.
Let's not throw our friendship away.

[Bridge]
The waiter's a real gentleman.
He gives us space and more coffee.
You look at me and finally speak.
I was so hurt, I shut you out.
I should have asked you face to face.
I'm damn glad you came tonight.
Fantastic, now we're both crying.
Let's start again, just you and me.

[Final Chorus]
Just be honest with me tonight.
I'm sorry, I made a mistake.
I'm not mad at you anymore.
I'm still your friend, I'm here to stay.

[Words used]: mom, mistake, hell, gentleman, fantastic, yesterday, god, lady, kill, shut, innocent, sorry, mad, honest, bunch, listen, damn
[Words left out]: president, terrorist, mate"""

# Clean draft as tab3 does
clean_draft = []
for line in user_input.splitlines():
    if line.strip().lower().startswith("[words used]") or line.strip().lower().startswith("[words left out]"):
        break
    clean_draft.append(line)
draft_to_process = "\n".join(clean_draft).strip()

target_words = ["mom", "mistake", "hell", "gentleman", "fantastic", "yesterday", "god", "lady", "kill", "shut", "innocent", "sorry", "mad", "honest", "bunch", "listen", "damn"]

print("Starting run_critic_only on full user song...")
t0 = time.time()
try:
    res = run_critic_only(
        draft=draft_to_process,
        target_words=target_words,
        theme="Street & Daily Life",
        genre="Cinematic / Ballad",
        concept="Two friends meet in a diner to apologize and clear up rumors."
    )
    t1 = time.time()
    print(f"Success in {round(t1 - t0, 1)}s!")
    print("Model:", res.get("model_used"))
    print("Overall Score:", res.get("overall_score"))
    print("Lines count:", len(res.get("line_breakdown", [])))
except Exception as e:
    print(f"Failed after {round(time.time() - t0, 1)}s with error: {e}")
