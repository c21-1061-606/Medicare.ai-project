
import sqlite3

conn = sqlite3.connect('diagnosis.db')
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS diagnoses (
    id INTEGER PRIMARY KEY,
    symptoms TEXT,
    diagnosis TEXT,
    date TEXT
)
''')
conn.commit()
conn.close()
