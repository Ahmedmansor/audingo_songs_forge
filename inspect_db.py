"""
inspect_db.py — Quick command-line viewer for ngsl_vocab.db
Run this anytime to see a summary of your database tables and recent activity.
"""

import sqlite3
import sys
from pathlib import Path

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = Path(__file__).parent / "ngsl_vocab.db"



def inspect():
    if not DB_PATH.exists():
        print(f"❌ Database file not found at {DB_PATH}. Run 'python build_db.py' first.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("📊 AUDINGO SONGS FORGE — DATABASE INSPECTION")
    print("=" * 60)

    # 1. Summary Stats
    cursor.execute("SELECT COUNT(*) FROM ngsl_words")
    total_ngsl = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM ngsl_words WHERE usage_count > 0")
    used_ngsl = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM extra_words")
    total_extra = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM songs")
    total_songs = cursor.fetchone()[0]

    print(f"• Total NGSL Headwords: {total_ngsl:,}")
    print(f"• Used NGSL Words:       {used_ngsl:,} ({(used_ngsl/total_ngsl*100) if total_ngsl else 0:.1f}%)")
    print(f"• Unused NGSL Words:     {total_ngsl - used_ngsl:,}")
    print(f"• Extra Words Tracked:   {total_extra:,}")
    print(f"• Saved Songs:           {total_songs:,}")
    print("-" * 60)

    # 2. POS Breakdown
    cursor.execute("SELECT pos_type, COUNT(*) as cnt FROM ngsl_words GROUP BY pos_type ORDER BY cnt DESC")
    print("\n📋 NGSL Parts of Speech Breakdown:")
    for row in cursor.fetchall():
        print(f"   - {row['pos_type']:<12}: {row['cnt']:,} words")

    # 3. Top Used NGSL Words
    cursor.execute("SELECT word, pos_type, usage_count FROM ngsl_words WHERE usage_count > 0 ORDER BY usage_count DESC LIMIT 10")
    top_used = cursor.fetchall()
    print("\n🔥 Top Used NGSL Words:")
    if top_used:
        for r in top_used:
            print(f"   - {r['word']} ({r['pos_type']}): used {r['usage_count']} time(s)")
    else:
        print("   (No words marked as used yet)")

    # 4. Top Extra Words
    cursor.execute("SELECT word, occurrence_count, first_seen_in_song FROM extra_words ORDER BY occurrence_count DESC LIMIT 10")
    top_extra = cursor.fetchall()
    print("\n🌟 Top Extra Words:")
    if top_extra:
        for r in top_extra:
            print(f"   - {r['word']}: {r['occurrence_count']} time(s) [First: '{r['first_seen_in_song']}']")
    else:
        print("   (No extra words tracked yet)")

    # 5. Recent Songs
    cursor.execute("SELECT id, title, target_words, created_at FROM songs ORDER BY id DESC LIMIT 5")
    recent_songs = cursor.fetchall()
    print("\n🎵 Recent Songs:")
    if recent_songs:
        for s in recent_songs:
            print(f"   [#{s['id']}] {s['title']} ({s['created_at']})")
            print(f"       Targets: {s['target_words']}")
    else:
        print("   (No songs saved yet)")

    print("=" * 60 + "\n")
    conn.close()


if __name__ == "__main__":
    inspect()
