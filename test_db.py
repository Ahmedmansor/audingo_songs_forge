import sqlite3
import json

try:
    conn = sqlite3.connect('ngsl_vocab.db')
    c = conn.cursor()
    c.execute("SELECT value FROM app_state WHERE key='refinement_state'")
    row = c.fetchone()
    if row:
        val = json.loads(row[0])
        print("Row exists!")
        print("Has draft:", bool(val.get('draft_input')))
        print("Has report:", bool(val.get('graph_report')))
    else:
        print("NO ROW FOUND FOR refinement_state!")
except Exception as e:
    print("ERROR:", e)
