# create_database.py
import sqlite3
import os

DB_PATH = "database.db"

# Ensure folders exist
os.makedirs("audio/arif_bhatti", exist_ok=True)
os.makedirs("audio/arnest_mall", exist_ok=True)
os.makedirs("audio/arslan_john", exist_ok=True)
os.makedirs("assets", exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# songs table
cur.execute("""
CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    singer TEXT NOT NULL,
    title TEXT NOT NULL,
    file_path TEXT NOT NULL
)
""")

# optional favorites table (simple)
cur.execute("""
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    song_id INTEGER,
    added_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY(song_id) REFERENCES songs(id)
)
""")

# clear previous sample rows (optional)
cur.execute("DELETE FROM songs")

# Sample seed data (ensure you add actual mp3 files to audio/ folders manually)
sample = [
    ("Arif_Bhatti", "Yesu Pyar Hai", "audio/arif_bhatti/yesu_pyar_hai.mp3"),
    ("Arif_Bhatti", "Tere Pyar Ne", "audio/arif_bhatti/tere_pyar_ne.mp3"),
    ("Arnest_Mall", "Masih Mera Sahara", "audio/arnest_mall/masih_mera_sahara.mp3"),
    ("Arnest_Mall", "Tu Mera Raja Hai", "audio/arnest_mall/tu_mera_raja_hai.mp3"),
    ("Arslan_John", "Yesu Mera Dost", "audio/arslan_john/yesu_mera_dost.mp3"),
    ("Arslan_John", "Rabb Di Rehmat", "audio/arslan_john/rabb_di_rehmat.mp3"),
]

cur.executemany("INSERT INTO songs (singer, title, file_path) VALUES (?, ?, ?)", sample)
conn.commit()
conn.close()

print("✅ database.db created/updated with sample data. Add mp3 files into audio/* folders.")
