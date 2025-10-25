import streamlit as st
from pathlib import Path
import os, sqlite3, base64, time
from streamlit_autorefresh import st_autorefresh

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="SoulFood 🎵", layout="centered", page_icon="🎶")

DB_PATH = "database.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def create_tables():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            singer TEXT,
            title TEXT,
            file_path TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER,
            FOREIGN KEY(song_id) REFERENCES songs(id)
        )
    """)
    conn.commit()
    conn.close()

# ---------------------- DATA ----------------------
SINGERS = {
    "arnest_mall": {"name": "Arnest Mall", "image": "assets/arnest_mall.jpeg", "folder": "audio/arnest_mall"},
    "arif_bhatti": {"name": "Arif Bhatti", "image": "assets/arif_bhatti.jpeg", "folder": "audio/arif_bhatti"},
    "arslan_john": {"name": "Arslan John", "image": "assets/ArslanJohn.jpeg", "folder": "audio/arslan_john"},
}

BIBLE_VERSES = [
    "🎵 Psalm 100:1 — Make a joyful noise unto the Lord, all ye lands.",
    "🎵 Isaiah 12:5 — Sing unto the Lord; for He hath done excellent things.",
    "🎵 Colossians 3:16 — Sing with grace in your hearts to the Lord.",
    "🎵 Psalm 95:1 — O come, let us sing unto the Lord!",
    "🎵 Ephesians 5:19 — Singing and making melody in your heart to the Lord.",
    "🎵 Psalm 33:3 — Sing unto Him a new song; play skilfully with a loud noise.",
    "🎵 Psalm 147:7 — Sing unto the Lord with thanksgiving.",
    "🎵 Psalm 104:33 — I will sing unto the Lord as long as I live.",
]

# ---------------------- AUTO SYNC ----------------------
def auto_sync_songs():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT file_path FROM songs")
    existing = {row[0] for row in cur.fetchall()}
    for key, data in SINGERS.items():
        folder = Path(data["folder"])
        folder.mkdir(parents=True, exist_ok=True)
        for file in folder.glob("*.mp3"):
            path = str(file)
            if path not in existing:
                title = file.stem.replace("_", " ").title()
                cur.execute("INSERT INTO songs (singer, title, file_path) VALUES (?, ?, ?)", (key, title, path))
    conn.commit()
    conn.close()

# ---------------------- CSS ----------------------
MOBILE_CSS = """
<style>
body, .block-container {
  max-width: 420px;
  margin: auto;
  padding: 8px;
  background: #f8fafc;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
}
.header {
  text-align: center;
  background: linear-gradient(135deg, #0b63d4, #5a9dfc);
  color: white;
  padding: 20px 10px;
  border-radius: 16px;
  margin-bottom: 10px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.1);
}
.title { font-size: 22px; font-weight: 800; margin-bottom: 4px; }
.verse-box { font-size: 13px; font-style: italic; opacity: 0.9; }

.song-card {
  background: white;
  border-radius: 14px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.05);
  padding: 10px 12px;
  margin-bottom: 10px;
}
.song-title { font-weight: 600; font-size: 15px; margin-bottom: 6px; }
.btn-row { display: flex; justify-content: space-around; gap: 8px; }

button[kind=primary] {
  width: 100%;
}

.bottom-nav {
  position: fixed;
  bottom: 90px;
  left: 0;
  right: 0;
  height: 56px;
  background: white;
  border-radius: 16px 16px 0 0;
  display: flex;
  justify-content: space-around;
  align-items: center;
  box-shadow: 0 -6px 20px rgba(0,0,0,0.1);
  z-index: 9999;
}

.bottom-nav button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
}

#sticky-player {
  position: fixed;
  bottom: 10px;
  left: 8px;
  right: 8px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
  padding: 6px 10px;
  display: none;
  justify-content: space-between;
  align-items: center;
  z-index: 9998;
}
</style>
"""

st.markdown(MOBILE_CSS, unsafe_allow_html=True)

# ---------------------- HELPERS ----------------------
def audio_data_url(file_path):
    try:
        with open(file_path, "rb") as f:
            b = base64.b64encode(f.read()).decode()
        return f"data:audio/mp3;base64,{b}"
    except: return None

# ---------------------- HEADER ----------------------
def show_header():
    st_autorefresh(interval=30000, key="refresh_verse")
    verse_index = int(time.time() / 30) % len(BIBLE_VERSES)
    verse = BIBLE_VERSES[verse_index]
    st.markdown(f"<div class='header'><div class='title'>🎵 SoulFood – پرستش 🎵</div><div class='verse-box'>{verse}</div></div>", unsafe_allow_html=True)

# ---------------------- PLAYER ----------------------
def show_player():
    pid = st.session_state.get("playing_song")
    if not pid: return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT title, file_path FROM songs WHERE id=?", (pid,))
    row = cur.fetchone()
    conn.close()
    if not row: return
    title, path = row
    url = audio_data_url(path)
    if not url: return
    player = f"""
    <div id="sticky-player" style="display:flex;">
        <div style="font-weight:600;">🎧 {title}</div>
        <audio id="sticky-audio" controls style="width:60%;">
            <source src="{url}" type="audio/mp3">
        </audio>
    </div>
    <script>document.getElementById('sticky-player').style.display='flex';</script>
    """
    st.markdown(player, unsafe_allow_html=True)

# ---------------------- MAIN ----------------------
create_tables(); auto_sync_songs()

if "view" not in st.session_state: st.session_state["view"] = "home"
if "selected_singer" not in st.session_state: st.session_state["selected_singer"] = None
if "playing_song" not in st.session_state: st.session_state["playing_song"] = None

# ---------------------- PAGES ----------------------
def show_home():
    show_header()
    st.markdown("### 🎤 Singers")
    for key, s in SINGERS.items():
        if st.button(f"🎶 {s['name']}", use_container_width=True):
            st.session_state["selected_singer"] = key
            st.session_state["view"] = "songs"
            st.experimental_rerun()

def show_songs():
    key = st.session_state["selected_singer"]
    show_header()
    songs = get_conn().execute("SELECT id, title, file_path FROM songs WHERE singer=?", (key,)).fetchall()
    if st.button("⬅️ Back", use_container_width=True):
        st.session_state["view"] = "home"
        st.experimental_rerun()
    for sid, title, path in songs:
        st.markdown(f"<div class='song-card'><div class='song-title'>{title}</div></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("▶️ Play", key=f"play_{sid}"):
                st.session_state["playing_song"] = sid
                st.experimental_rerun()
        with c2:
            if st.button("🗑️ Delete", key=f"del_{sid}"):
                os.remove(path)
                get_conn().execute("DELETE FROM songs WHERE id=?", (sid,))
                get_conn().commit()
                st.experimental_rerun()

def show_upload():
    show_header()
    with st.form("upload", clear_on_submit=True):
        singer = st.selectbox("🎤 Select Singer", list(SINGERS.keys()), format_func=lambda x: SINGERS[x]["name"])
        title = st.text_input("Song Title")
        file = st.file_uploader("Upload MP3", type=["mp3"])
        if st.form_submit_button("Upload"):
            if not file or not title:
                st.error("⚠️ Fill all fields")
            else:
                dest = Path(SINGERS[singer]["folder"]) / file.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                with open(dest, "wb") as f: f.write(file.getbuffer())
                get_conn().execute("INSERT INTO songs (singer, title, file_path) VALUES (?, ?, ?)", (singer, title, str(dest)))
                get_conn().commit()
                st.success("✅ Uploaded!")
                st.experimental_rerun()

# ---------------------- ROUTER ----------------------
if st.session_state["view"] == "home": show_home()
elif st.session_state["view"] == "songs": show_songs()
elif st.session_state["view"] == "upload": show_upload()

# ---------------------- BOTTOM NAV ----------------------
nav = """
<div class='bottom-nav'>
  <button onclick="window.location.reload()">🏠</button>
  <button onclick="window.scrollTo(0,0)">❤️</button>
  <button onclick="window.scrollTo(0,0)">⬆️</button>
</div>
"""
st.markdown(nav, unsafe_allow_html=True)
show_player()
