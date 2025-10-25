import streamlit as st
from pathlib import Path
import os
import sqlite3
import base64
import time
from streamlit_autorefresh import st_autorefresh

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="SoulFood 🎵", layout="wide", page_icon="🎶")

# ---------------------- DATABASE ----------------------
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

# ---------------------- DATA -----------------------
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
    "🎵 1 Chronicles 16:9 — Sing unto Him, sing psalms unto Him.",
    "🎵 Psalm 13:6 — I will sing unto the Lord, because He hath dealt bountifully with me.",
    "🎵 Psalm 104:33 — I will sing unto the Lord as long as I live.",
]

# ---------------------- AUTO SYNC ------------------
def auto_sync_songs():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT file_path FROM songs")
    existing_files = {row[0] for row in cur.fetchall()}

    for key, data in SINGERS.items():
        folder = Path(data["folder"])
        folder.mkdir(parents=True, exist_ok=True)
        for file in folder.glob("*.mp3"):
            file_str = str(file)
            if file_str not in existing_files:
                title = file.stem.replace("_", " ").title()
                cur.execute(
                    "INSERT INTO songs (singer, title, file_path) VALUES (?, ?, ?)",
                    (key, title, file_str),
                )
    conn.commit()
    conn.close()

# ---------------------- UTILS ----------------------
def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            b64 = base64.b64encode(img_file.read()).decode()
        ext = Path(image_path).suffix.replace(".", "").lower()
        if ext not in ("jpg", "jpeg", "png", "gif"):
            ext = "jpeg"
        return f"data:image/{ext};base64,{b64}"
    except Exception:
        return ""

def get_songs_by_singer(singer_key):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, file_path FROM songs WHERE singer=?", (singer_key,))
    songs = cur.fetchall()
    conn.close()
    return songs

def get_favorites():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT song_id FROM favorites")
    fav_ids = [row[0] for row in cur.fetchall()]
    conn.close()
    return fav_ids

def toggle_favorite(song_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM favorites WHERE song_id=?", (song_id,))
    exists = cur.fetchone()
    if exists:
        cur.execute("DELETE FROM favorites WHERE song_id=?", (song_id,))
        msg = "💔 Removed from favorites"
    else:
        cur.execute("INSERT INTO favorites (song_id) VALUES (?)", (song_id,))
        msg = "❤️ Added to favorites"
    conn.commit()
    conn.close()
    try:
        st.toast(msg)
    except Exception:
        st.success(msg)

def delete_song(song_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT file_path FROM songs WHERE id=?", (song_id,))
    file_path_row = cur.fetchone()
    if file_path_row:
        file_path = file_path_row[0]
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
    cur.execute("DELETE FROM songs WHERE id=?", (song_id,))
    cur.execute("DELETE FROM favorites WHERE song_id=?", (song_id,))
    conn.commit()
    conn.close()
    st.success("🗑️ Song deleted successfully!")
    if st.session_state.get("playing_song") == song_id:
        st.session_state["playing_song"] = None
    st.experimental_rerun()

def audio_data_url(file_path):
    try:
        with open(file_path, "rb") as f:
            b = f.read()
        b64 = base64.b64encode(b).decode()
        return f"data:audio/mp3;base64,{b64}"
    except Exception:
        return None

# ---------------------- CSS ------------------------
BASE_CSS = """
<style>
:root {
  --bg: #f6f9fc;
  --card: #ffffff;
  --muted: #5b6876;
  --primary: #0b63d4;
  --text: #0b1730;
  --shadow: rgba(2,6,23,0.06);
}
section[data-testid="stSidebar"] { display: none !important; }
div.block-container { padding: 10px; }
body { background-color: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial; }

/* header */
.header { text-align:center; margin:6px 0; }
.title { color: var(--primary); font-weight:800; margin-bottom:4px; font-size:22px; }
.verse-box { background-color:#e8f0fe; border-left:5px solid var(--primary); border-radius:10px; padding:10px; text-align:center; font-style:italic; font-size:14px; margin-top:8px; }

/* sticky player */
#sticky-player {
  position: fixed;
  bottom: 8px;
  left: 10px;
  right: 10px;
  background: var(--card);
  border-radius: 14px;
  padding: 8px 10px;
  box-shadow: 0 10px 40px var(--shadow);
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 9998;
}

/* bottom nav */
.bottom-nav {
  position: fixed;
  bottom: 90px; /* moved up so it appears above sticky player */
  left: 8px;
  right: 8px;
  height: 56px;
  background: white;
  display: flex;
  justify-content: space-around;
  align-items: center;
  box-shadow: 0 -6px 20px rgba(2,6,23,0.06);
  border-radius: 12px;
  z-index: 9999;
}
.bottom-nav button {
  background: none;
  border: none;
  font-size: 22px;
  cursor: pointer;
}
.bottom-nav button:hover {
  transform: scale(1.2);
}
</style>
"""

# ---------------------- HEADER ----------------------
def show_header():
    st_autorefresh(interval=30000, key="verse_refresh")
    st.markdown("<div class='header'>", unsafe_allow_html=True)
    st.markdown("<h1 class='title'>🎵 SoulFood – پرستش 🎵</h1>", unsafe_allow_html=True)
    verse_index = int(time.time() / 30) % len(BIBLE_VERSES)
    verse = BIBLE_VERSES[verse_index]
    st.markdown(f"<div class='verse-box'>{verse}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---", unsafe_allow_html=True)

# ---------------------- STICKY PLAYER ----------------------
def show_sticky_player_if_playing():
    playing_id = st.session_state.get("playing_song")
    if not playing_id:
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT title, file_path FROM songs WHERE id=?", (playing_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return
    title, file_path = row
    if not file_path or not os.path.exists(file_path):
        return

    data_url = audio_data_url(file_path)
    if not data_url:
        return

    player_html = f"""
    <div id="sticky-player" style="display:flex; gap:12px; align-items:center; justify-content:space-between;">
      <div style="font-weight:700; min-width:120px; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">
        🎧 {title}
      </div>
      <audio id="sticky-audio" controls style="max-width:58%; width:58%;">
        <source src="{data_url}" type="audio/mp3">
      </audio>
      <div style="min-width:80px; display:flex; gap:6px; justify-content:center;">
        <button onclick="document.getElementById('sticky-audio').pause();" style="padding:8px;border-radius:8px;">⏸️</button>
        <button onclick="document.getElementById('sticky-audio').play();" style="padding:8px;border-radius:8px;">▶️</button>
      </div>
    </div>
    <script>const p=document.getElementById('sticky-player');if(p)p.style.display='flex';</script>
    """
    st.markdown(player_html, unsafe_allow_html=True)

# ---------------------- MAIN APP ----------------------
create_tables()
auto_sync_songs()

if "selected_singer" not in st.session_state:
    st.session_state["selected_singer"] = None
if "show_favorites" not in st.session_state:
    st.session_state["show_favorites"] = False
if "playing_song" not in st.session_state:
    st.session_state["playing_song"] = None
if "view" not in st.session_state:
    st.session_state["view"] = "home"

st.markdown(BASE_CSS, unsafe_allow_html=True)

# ---------------------- NAVIGATION BAR ----------------------
nav_placeholder = st.empty()
with nav_placeholder.container():
    st.markdown('<div class="bottom-nav">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🏠", key="nav_home"):
            st.session_state["view"] = "home"
            st.session_state["selected_singer"] = None
            st.session_state["show_favorites"] = False
            st.experimental_rerun()
    with col2:
        if st.button("❤️", key="nav_fav"):
            st.session_state["view"] = "favorites"
            st.session_state["selected_singer"] = None
            st.session_state["show_favorites"] = True
            st.experimental_rerun()
    with col3:
        if st.button("⬆️", key="nav_upload"):
            st.session_state["view"] = "upload"
            st.session_state["selected_singer"] = None
            st.session_state["show_favorites"] = False
            st.experimental_rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------- ROUTING ----------------------
from random import choice

def show_singers():
    show_header()
    st.info("📱 Tap a singer to open their songs. Use the bottom bar for navigation.")
    for key, data in SINGERS.items():
        st.markdown(f"### 🎤 {data['name']}")
        if st.button(f"Open {data['name']}", key=f"open_{key}"):
            st.session_state["selected_singer"] = key
            st.session_state["view"] = "songs"
            st.experimental_rerun()

def show_songs(singer_key):
    show_header()
    songs = get_songs_by_singer(singer_key)
    fav_ids = get_favorites()
    if st.button("⬅️ Back"):
        st.session_state["selected_singer"] = None
        st.session_state["view"] = "home"
        st.experimental_rerun()
    for song_id, title, file_path in songs:
        fav_heart = "❤️" if song_id in fav_ids else "🤍"
        st.markdown(f"**🎵 {title}**")
        if st.session_state.get("playing_song") == song_id:
            st.audio(open(file_path, "rb").read(), format="audio/mp3")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("▶️ Play" if st.session_state.get("playing_song") != song_id else "⏸️ Stop", key=f"play_{song_id}"):
                st.session_state["playing_song"] = None if st.session_state.get("playing_song") == song_id else song_id
                st.experimental_rerun()
        with c2:
            if st.button(fav_heart + " Fav", key=f"fav_{song_id}"):
                toggle_favorite(song_id)
                st.experimental_rerun()
        with c3:
            if st.button("🗑️ Delete", key=f"del_{song_id}"):
                delete_song(song_id)

def show_favorites_view():
    show_header()
    fav_ids = get_favorites()
    if not fav_ids:
        st.info("No favorites yet ❤️")
        return
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT id, title, file_path FROM songs WHERE id IN ({','.join(['?']*len(fav_ids))})", fav_ids)
    songs = cur.fetchall()
    conn.close()
    for song_id, title, file_path in songs:
        st.markdown(f"**🎵 {title}**")
        if st.button("▶️ Play", key=f"playfav_{song_id}"):
            st.session_state["playing_song"] = song_id
            st.experimental_rerun()

def show_upload_page():
    show_header()
    with st.form("upload_form", clear_on_submit=True):
        singer_choice = st.selectbox("Select Singer", list(SINGERS.keys()), format_func=lambda x: SINGERS[x]["name"])
        song_title = st.text_input("Song Title")
        uploaded_file = st.file_uploader("Upload MP3", type=["mp3"])
        if st.form_submit_button("Upload"):
            if not uploaded_file or not song_title:
                st.error("⚠️ Missing details!")
            else:
                dest_folder = Path(SINGERS[singer_choice]["folder"])
                dest_folder.mkdir(parents=True, exist_ok=True)
                dest = dest_folder / uploaded_file.name
                with open(dest, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                conn = get_conn()
                conn.execute("INSERT INTO songs (singer, title, file_path) VALUES (?, ?, ?)", (singer_choice, song_title, str(dest)))
                conn.commit()
                conn.close()
                st.success("✅ Uploaded successfully!")
                auto_sync_songs()
                st.experimental_rerun()

# ---------------------- ROUTING ----------------------
if st.session_state["view"] == "home":
    if st.session_state["selected_singer"]:
        show_songs(st.session_state["selected_singer"])
    else:
        show_singers()
elif st.session_state["view"] == "favorites":
    show_favorites_view()
elif st.session_state["view"] == "upload":
    show_upload_page()

# ---------------------- SHOW PLAYER ----------------------
show_sticky_player_if_playing()
