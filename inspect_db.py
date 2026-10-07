import sqlite3
import json

conn = sqlite3.connect('ngsl_vocab.db')
c = conn.cursor()
c.execute("SELECT value FROM app_state WHERE key='refinement_state'")
row = c.fetchone()
val = json.loads(row[0])
gr = val.get('graph_report')
print('TYPE:', type(gr))
if gr:
    print('IS DICT:', isinstance(gr, dict))
    print('KEYS:', list(gr.keys()))
else:
    print('IT IS NONE OR EMPTY!')
