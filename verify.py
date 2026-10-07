import sqlite3
conn = sqlite3.connect('ngsl_vocab.db')
cursor = conn.cursor()
cursor.execute("SELECT count(*) FROM songs")
count = cursor.fetchone()[0]
with open('verify_count.txt', 'w') as f:
    f.write(str(count))
conn.close()
