import sqlite3
import pandas as pd

try:
    conn = sqlite3.connect('ngsl_vocab.db')
    df = pd.read_sql_query('SELECT id, title FROM songs', conn)
    with open('dump.txt', 'w', encoding='utf-8') as f:
        f.write(f"Count: {len(df)}\n")
        f.write(df.to_string())
except Exception as e:
    with open('dump.txt', 'w', encoding='utf-8') as f:
        f.write(str(e))
