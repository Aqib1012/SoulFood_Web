# soulfood_mobile_ui.py
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
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            singer TEXT,
            title TEXT,
            file_path TEXT
        )
    """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER,
            FOREIGN KEY(song_id) REFERENCES songs(id)
        )
    """
    )
    conn.commit()
    conn.close()


# ---------------------- DATA -----------------------
SINGERS = {
    "arnest_mall": {
        "name": "Arnest Mall",
        "image": "assets/arnest_mall.jpeg",
        "folder": "audio/arnest_mall",
    },
    "arif_bhatti": {
        "name": "Arif Bhatti",
        "image": "assets/arif_bhatti.jpeg",
        "folder": "audio/arif_bhatti",
    },
    "arslan_john": {
        "name": "Arslan John",
        "image": "assets/ArslanJohn.jpeg",
        "folder": "audio/arslan_john",
    },
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
    """
    Scans singer folders for .mp3 files and inserts them into the songs table if missing.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT file_path FROM songs")
    existing_files = {row[0] for row in cur.fetchall()}

    for key, data in SINGERS.items():
        folder = Path(data["folder"])
        folder.mkdir(parents=True, exist_ok=True)
        for file in folder.glob("*.mp3"):
            # normalize path string
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
    st.rerun()


def audio_data_url(file_path):
    """Return a data URL for an mp3 file to use in an HTML audio tag (base64)."""
    try:
        with open(file_path, "rb") as f:
            b = f.read()
        b64 = base64.b64encode(b).decode()
        return f"data:audio/mp3;base64,{b64}"
    except Exception:
        return None


# ---------------------- MOBILE / NATIVE-LIKE CSS ------------------------
MOBILE_CSS = """
<style>
:root{
  --bg: linear-gradient(180deg,#0f172a 0%, #071032 100%);
  --card: #0b1220;
  --muted: #93a3b8;
  --accent: #7dd3fc;
  --accent-2: #60a5fa;
  --glass: rgba(255,255,255,0.03);
  --pill: rgba(255,255,255,0.04);
  --shadow: rgba(2,6,23,0.65);
  --text: #e6eef8;
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
}

/* Page container adjusted for mobile app feel */
.block-container {
  padding-top: 10px;
  padding-left: 10px;
  padding-right: 10px;
  max-width: 430px;
  margin-left: auto;
  margin-right: auto;
}

/* App header */
.app-header {
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  padding:12px 8px;
  border-radius:14px;
  background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  box-shadow: 0 8px 30px rgba(0,0,0,0.6);
  margin-bottom: 10px;
}
.app-title {
  font-size:20px;
  font-weight:800;
  letter-spacing:0.4px;
  color:var(--text);
}
.verse-pill {
  background: linear-gradient(90deg, rgba(125,211,252,0.12), rgba(96,165,250,0.08));
  padding:8px 12px;
  border-radius:999px;
  font-size:13px;
  color:var(--text);
  box-shadow: 0 6px 18px rgba(6,10,24,0.55);
}

/* Singer card (rounded) */
.singer-grid {
  display:grid;
  grid-template-columns: repeat(2, 1fr);
  gap:10px;
  margin-bottom: 12px;
}
.singer-card {
  background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  border-radius:18px;
  padding:14px;
  text-align:center;
  box-shadow: 0 12px 30px rgba(2,6,23,0.5);
  transition: transform .18s ease;
  cursor: pointer;
}
.singer-card:active { transform: translateY(3px) scale(0.995); }
.singer-card img { width:82px; height:82px; border-radius:50%; object-fit:cover; border: 3px solid rgba(125,211,252,0.12); margin-bottom:8px; }

/* Song list */
.song-list { display:flex; flex-direction:column; gap:10px; margin-bottom:80px; }
.song-tile {
  display:flex; align-items:center; gap:12px; justify-content:space-between;
  background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  padding:12px; border-radius:14px; box-shadow: 0 8px 20px rgba(2,6,23,0.45);
}
.song-info { flex:1; min-width:0; }
.song-title { font-weight:700; font-size:15px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.song-sub { color:var(--muted); font-size:13px; margin-top:4px; }

/* Floating sticky player (rounded pill) */
#sticky-player {
  position:fixed; left:50%; transform:translateX(-50%); bottom:78px;
  width:92%; max-width:430px; border-radius:999px; padding:10px 14px;
  background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  box-shadow: 0 18px 40px rgba(2,6,23,0.6);
  display:none; align-items:center; gap:12px; z-index:9999;
}
#sticky-player .title { font-weight:800; color:var(--text); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

/* Bottom navigation */
.bottom-nav {
  position:fixed; left:50%; transform:translateX(-50%); bottom:12px;
  width:94%; max-width:430px; display:flex; justify-content:space-between; gap:8px;
  padding:8px; border-radius:18px; background: linear-gradient(90deg, rgba(3,7,18,0.7), rgba(3,7,18,0.55));
  box-shadow: 0 10px 30px rgba(2,6,23,0.7); z-index:10000;
}
.bottom-btn {
  flex:1; display:flex; align-items:center; justify-content:center; gap:8px;
  padding:10px 8px; border-radius:12px; cursor:pointer; color:var(--muted);
  border: none; background:transparent; font-weight:700;
}
.bottom-btn.active { color:var(--accent); background: linear-gradient(90deg, rgba(125,211,252,0.06), rgba(96,165,250,0.04)); box-shadow: inset 0 -2px 8px rgba(125,211,252,0.02); }

/* Admin bottom sheet */
.admin-sheet {
  position:fixed; left:50%; transform:translateX(-50%); bottom:0;
  width:100%; max-width:430px; border-top-left-radius:18px; border-top-right-radius:18px;
  background:linear-gradient(180deg, rgba(8,13,25,0.95), rgba(6,10,18,0.98)); padding:14px;
  box-shadow: 0 -6px 40px rgba(2,6,23,0.8); z-index:10001;
}

/* Responsive adjustments */
@media(min-width:900px){
  .singer-grid { grid-template-columns: repeat(3, 1fr); }
}
</style>
"""

# ---------------------- HEADER / PLAYER HELPERS ----------------------
def show_header(compact=False):
    # Auto refresh every 30s for verse
    # soulfood_mobile_ui.py
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
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            singer TEXT,
            title TEXT,
            file_path TEXT
        )
    """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id INTEGER,
            FOREIGN KEY(song_id) REFERENCES songs(id)
        )
    """
    )
    conn.commit()
    conn.close()


# ---------------------- DATA -----------------------
SINGERS = {
    "arnest_mall": {
        "name": "Arnest Mall",
        "image": "assets/arnest_mall.jpeg",
        "folder": "audio/arnest_mall",
    },
    "arif_bhatti": {
        "name": "Arif Bhatti",
        "image": "assets/arif_bhatti.jpeg",
        "folder": "audio/arif_bhatti",
    },
    "arslan_john": {
        "name": "Arslan John",
        "image": "assets/ArslanJohn.jpeg",
        "folder": "audio/arslan_john",
    },
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
    """
    Scans singer folders for .mp3 files and inserts them into the songs table if missing.
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT file_path FROM songs")
    existing_files = {row[0] for row in cur.fetchall()}

    for key, data in SINGERS.items():
        folder = Path(data["folder"])
        folder.mkdir(parents=True, exist_ok=True)
        for file in folder.glob("*.mp3"):
            # normalize path string
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
    st.rerun()


def audio_data_url(file_path):
    """Return a data URL for an mp3 file to use in an HTML audio tag (base64)."""
    try:
        with open(file_path, "rb") as f:
            b = f.read()
        b64 = base64.b64encode(b).decode()
        return f"data:audio/mp3;base64,{b64}"
    except Exception:
        return None


# ---------------------- MOBILE / NATIVE-LIKE CSS ------------------------
MOBILE_CSS = """
<style>
:root{
  --bg: linear-gradient(180deg,#0f172a 0%, #071032 100%);
  --card: #0b1220;
  --muted: #93a3b8;
  --accent: #7dd3fc;
  --accent-2: #60a5fa;
  --glass: rgba(255,255,255,0.03);
  --pill: rgba(255,255,255,0.04);
  --shadow: rgba(2,6,23,0.65);
  --text: #e6eef8;
}

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
}

/* Page container adjusted for mobile app feel */
.block-container {
  padding-top: 10px;
  padding-left: 10px;
  padding-right: 10px;
  max-width: 430px;
  margin-left: auto;
  margin-right: auto;
}

/* App header */
.app-header {
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  padding:12px 8px;
  border-radius:14px;
  background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  box-shadow: 0 8px 30px rgba(0,0,0,0.6);
  margin-bottom: 10px;
}
.app-title {
  font-size:20px;
  font-weight:800;
  letter-spacing:0.4px;
  color:var(--text);
}
.verse-pill {
  background: linear-gradient(90deg, rgba(125,211,252,0.12), rgba(96,165,250,0.08));
  padding:8px 12px;
  border-radius:999px;
  font-size:13px;
  color:var(--text);
  box-shadow: 0 6px 18px rgba(6,10,24,0.55);
}

/* Singer card (rounded) */
.singer-grid {
  display:grid;
  grid-template-columns: repeat(2, 1fr);
  gap:10px;
  margin-bottom: 12px;
}
.singer-card {
  background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  border-radius:18px;
  padding:14px;
  text-align:center;
  box-shadow: 0 12px 30px rgba(2,6,23,0.5);
  transition: transform .18s ease;
  cursor: pointer;
}
.singer-card:active { transform: translateY(3px) scale(0.995); }
.singer-card img { width:82px; height:82px; border-radius:50%; object-fit:cover; border: 3px solid rgba(125,211,252,0.12); margin-bottom:8px; }

/* Song list */
.song-list { display:flex; flex-direction:column; gap:10px; margin-bottom:80px; }
.song-tile {
  display:flex; align-items:center; gap:12px; justify-content:space-between;
  background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  padding:12px; border-radius:14px; box-shadow: 0 8px 20px rgba(2,6,23,0.45);
}
.song-info { flex:1; min-width:0; }
.song-title { font-weight:700; font-size:15px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.song-sub { color:var(--muted); font-size:13px; margin-top:4px; }

/* Floating sticky player (rounded pill) */
#sticky-player {
  position:fixed; left:50%; transform:translateX(-50%); bottom:78px;
  width:92%; max-width:430px; border-radius:999px; padding:10px 14px;
  background: linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  box-shadow: 0 18px 40px rgba(2,6,23,0.6);
  display:none; align-items:center; gap:12px; z-index:9999;
}
#sticky-player .title { font-weight:800; color:var(--text); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

/* Bottom navigation */
.bottom-nav {
  position:fixed; left:50%; transform:translateX(-50%); bottom:12px;
  width:94%; max-width:430px; display:flex; justify-content:space-between; gap:8px;
  padding:8px; border-radius:18px; background: linear-gradient(90deg, rgba(3,7,18,0.7), rgba(3,7,18,0.55));
  box-shadow: 0 10px 30px rgba(2,6,23,0.7); z-index:10000;
}
.bottom-btn {
  flex:1; display:flex; align-items:center; justify-content:center; gap:8px;
  padding:10px 8px; border-radius:12px; cursor:pointer; color:var(--muted);
  border: none; background:transparent; font-weight:700;
}
.bottom-btn.active { color:var(--accent); background: linear-gradient(90deg, rgba(125,211,252,0.06), rgba(96,165,250,0.04)); box-shadow: inset 0 -2px 8px rgba(125,211,252,0.02); }

/* Admin bottom sheet */
.admin-sheet {
  position:fixed; left:50%; transform:translateX(-50%); bottom:0;
  width:100%; max-width:430px; border-top-left-radius:18px; border-top-right-radius:18px;
  background:linear-gradient(180deg, rgba(8,13,25,0.95), rgba(6,10,18,0.98)); padding:14px;
  box-shadow: 0 -6px 40px rgba(2,6,23,0.8); z-index:10001;
}

/* Responsive adjustments */
@media(min-width:900px){
  .singer-grid { grid-template-columns: repeat(3, 1fr); }
}
</style>
"""

# ---------------------- HEADER / PLAYER HELPERS ----------------------
def show_header(compact=False):
    # Auto refresh every 30s for verse
    unique_page = (
    "home" if not st.session_state.get("selected_singer") 
    else st.session_state["selected_singer"]
)
if st.session_state.get("show_favorites"):
    unique_page = "favorites"

st_autorefresh(interval=30000, key=f"verse_refresh_{unique_page}_{int(time.time() * 1000) % 1000}")

    verse_index = int(time.time() / 30) % len(BIBLE_VERSES)
    verse = BIBLE_VERSES[verse_index]
    st.markdown(
        f"""
        <div class='app-header'>
          <div style='display:flex; align-items:center; gap:10px;'>
            <img src="data:image/svg+xml;base64,{base64.b64encode(HEADER_SVG.encode()).decode()}" style="width:38px;height:38px;border-radius:10px;"/>
            <div class='app-title'>SoulFood</div>
          </div>
          <div class='verse-pill'>{verse}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# small inline SVG used for header icon (keeps external assets unchanged)
HEADER_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none'><rect width='24' height='24' rx='5' fill='#0b1220'/><path d='M9 9v6.5A3.5 3.5 0 1 0 15.5 19V8' stroke='url(#g)' stroke-width='1.2' stroke-linecap='round' stroke-linejoin='round'/><defs><linearGradient id='g' x1='0' x2='1'><stop offset='0' stop-color='#7dd3fc'/><stop offset='1' stop-color='#60a5fa'/></linearGradient></defs></svg>"""

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
        st.warning("⚠️ Playing file missing.")
        return

    data_url = audio_data_url(file_path)
    if not data_url:
        st.warning("⚠️ Cannot load audio for sticky player.")
        return

    player_html = f"""
    <div id="sticky-player" style="display:flex;">
      <div style="font-weight:800; min-width:140px; max-width:45%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
        🎧 {title}
      </div>
      <audio id="sticky-audio" controls style="flex:1; max-width:55%;">
        <source src="{data_url}" type="audio/mp3">
        Your browser does not support the audio element.
      </audio>
    </div>
    <script>
      const p = document.getElementById('sticky-player');
      if (p) p.style.display = 'flex';
    </script>
    """
    st.markdown(player_html, unsafe_allow_html=True)


# ---------------------- VIEWS (UI only changed) ----------------------
def show_singers():
    show_header()
    st.markdown(
        "<div style='margin-top:6px; font-weight:700; color:var(--muted); margin-bottom:6px;'>Choose a singer</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="singer-grid">', unsafe_allow_html=True)
    for key, data in SINGERS.items():
        img_src = image_to_base64(data["image"]) if os.path.exists(data["image"]) else ""
        # Each singer card uses a button to open singer view (keeps old behavior)
        st.markdown(
            f"""
            <div class="singer-card" onclick="document.querySelector('button[kind=open_{key}]')?.click()">
                <img src="{img_src}" alt="{data['name']}">
                <div style="font-weight:800; margin-top:6px;">{data['name']}</div>
                <div style="margin-top:6px; color:var(--muted); font-weight:600; font-size:13px;">Tap to open</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Open {data['name']}", key=f"open_{key}"):
            st.session_state["selected_singer"] = key
            st.session_state["show_favorites"] = False
            st.session_state["playing_song"] = None
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def show_songs(singer_key):
    show_header()
    songs = get_songs_by_singer(singer_key)
    fav_ids = get_favorites()

    st.markdown(f"<div style='font-weight:800; font-size:18px; margin-bottom:6px;'>{SINGERS[singer_key]['name']}</div>", unsafe_allow_html=True)

    if st.button("⬅️ Back", key="back_top"):
        st.session_state["selected_singer"] = None
        st.session_state["playing_song"] = None
        st.session_state["show_favorites"] = False
        st.rerun()

    if not songs:
        st.info("No songs found for this singer.")
        return

    st.markdown('<div class="song-list">', unsafe_allow_html=True)

    for song_id, title, file_path in songs:
        fav_heart = "❤️" if song_id in fav_ids else "🤍"
        # Song tile
        st.markdown("<div class='song-tile'>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class='song-info'>
              <div class='song-title'>🎵 {title}</div>
              <div class='song-sub'>{SINGERS[singer_key]['name']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Buttons column (Play / Favorite / Delete)
        col_html = """
        <div style='display:flex; gap:8px; align-items:center;'>
        """
        st.markdown(col_html, unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.session_state.get("playing_song") == song_id:
                if st.button("⏸️", key=f"stop_{song_id}"):
                    st.session_state["playing_song"] = None
                    st.rerun()
            else:
                if st.button("▶️", key=f"play_{song_id}"):
                    st.session_state["playing_song"] = song_id
                    st.rerun()
        with c2:
            if st.button(fav_heart, key=f"fav_{song_id}"):
                toggle_favorite(song_id)
                st.rerun()
        with c3:
            if st.button("🗑️", key=f"del_{song_id}"):
                delete_song(song_id)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def show_favorites_view():
    show_header()
    fav_ids = get_favorites()

    if not fav_ids:
        st.info("No favorites yet! Add some songs you love ❤️")
        return

    conn = get_conn()
    cur = conn.cursor()
    placeholders = ",".join(["?"] * len(fav_ids))
    cur.execute(f"SELECT id, title, file_path, singer FROM (SELECT id, title, file_path, singer FROM songs) WHERE id IN ({placeholders})", fav_ids)
    favs = cur.fetchall()
    conn.close()

    st.markdown("<div style='font-weight:800; font-size:18px; margin-bottom:6px;'>❤️ Favorites</div>", unsafe_allow_html=True)

    for song_id, title, file_path, _ in favs:
        st.markdown(
            f"<div class='song-tile'><div class='song-info'><div class='song-title'>🎵 {title}</div></div>",
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.session_state.get("playing_song") == song_id:
                if st.button("⏸️", key=f"stopfav_{song_id}"):
                    st.session_state["playing_song"] = None
                    st.rerun()
            else:
                if st.button("▶️", key=f"playfav_{song_id}"):
                    st.session_state["playing_song"] = song_id
                    st.rerun()
        with c2:
            if st.button("💔", key=f"remove_fav_{song_id}"):
                toggle_favorite(song_id)
                st.rerun()
            if st.button("🗑️", key=f"delete_fav_{song_id}"):
                delete_song(song_id)
        st.markdown("</div>", unsafe_allow_html=True)


# Admin view (same upload form & add singer flow as original, moved into main admin sheet)
def show_admin_sheet():
    st.markdown("<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'><div style='font-weight:800; font-size:18px;'>➕ Admin</div><div style='color:var(--muted); font-weight:700;'>Upload & Manage</div></div>", unsafe_allow_html=True)
    with st.expander("➕ Add Singer (optional)", expanded=False):
        new_singer_key = st.text_input("Singer key (slug, e.g., john_doe)", key="admin_new_singer_key")
        new_singer_name = st.text_input("Singer name", key="admin_new_singer_name")
        new_singer_img = st.text_input("Image path (optional)", key="admin_new_singer_img")
        new_singer_folder = st.text_input("Folder path (optional, default audio/<key>)", key="admin_new_singer_folder")
        if st.button("Add Singer", key="admin_add_singer"):
            if not new_singer_key or not new_singer_name:
                st.error("Please provide both key and name.")
            else:
                key = new_singer_key.strip()
                folder = new_singer_folder.strip() or f"audio/{key}"
                SINGERS[key] = {"name": new_singer_name.strip(), "image": new_singer_img.strip() or "", "folder": folder}
                Path(folder).mkdir(parents=True, exist_ok=True)
                st.success(f"Added singer {new_singer_name}")
                st.experimental_rerun()

    st.markdown("---")
    with st.form("upload_form_main", clear_on_submit=True):
        singer_choice = st.selectbox("Select Singer", list(SINGERS.keys()), format_func=lambda x: SINGERS[x]["name"], key="admin_singer_choice")
        song_title = st.text_input("Song Title", key="admin_song_title")
        uploaded_file = st.file_uploader("Upload MP3 File", type=["mp3"], key="admin_upload")
        submitted = st.form_submit_button("Upload Song")
        if submitted:
            if not uploaded_file:
                st.error("⚠️ Please choose an MP3 file to upload.")
            elif not song_title:
                st.error("⚠️ Please enter the song title.")
            else:
                dest_folder = Path(SINGERS[singer_choice]["folder"])
                dest_folder.mkdir(parents=True, exist_ok=True)
                safe_name = uploaded_file.name.replace(" ", "_")
                dest_path = dest_folder / safe_name
                if dest_path.exists():
                    stem = dest_path.stem
                    suffix = dest_path.suffix
                    dest_path = dest_folder / f"{stem}_{int(time.time())}{suffix}"
                with open(dest_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("INSERT INTO songs (singer, title, file_path) VALUES (?, ?, ?)", (singer_choice, song_title, str(dest_path)))
                conn.commit()
                conn.close()
                st.success(f"✅ Song '{song_title}' uploaded successfully!")
                time.sleep(0.5)
                auto_sync_songs()
                st.experimental_rerun()


# ---------------------- APP START ------------------
create_tables()
auto_sync_songs()

if "selected_singer" not in st.session_state:
    st.session_state["selected_singer"] = None
if "show_favorites" not in st.session_state:
    st.session_state["show_favorites"] = False
if "playing_song" not in st.session_state:
    st.session_state["playing_song"] = None
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "home"
if "show_admin_sheet" not in st.session_state:
    st.session_state["show_admin_sheet"] = False

# Insert CSS
st.markdown(MOBILE_CSS, unsafe_allow_html=True)

# Main container (mobile-width)
st.markdown("<div class='block-container'>", unsafe_allow_html=True)

# Top header
show_header()

# Decide which main content to show (home / favorites / singer / admin)
if st.session_state["active_tab"] == "home" and not st.session_state["selected_singer"] and not st.session_state["show_favorites"]:
    show_singers()
elif st.session_state["active_tab"] == "favorites" or st.session_state.get("show_favorites"):
    st.session_state["active_tab"] = "favorites"
    st.session_state["show_favorites"] = True
    show_favorites_view()
elif st.session_state["selected_singer"]:
    show_songs(st.session_state["selected_singer"])
elif st.session_state["active_tab"] == "admin" or st.session_state.get("show_admin_sheet"):
    st.session_state["active_tab"] = "admin"
    show_admin_sheet()
else:
    show_singers()

st.markdown("</div>", unsafe_allow_html=True)

# Sticky bottom player
show_sticky_player_if_playing()

# Bottom navigation (native-like)
nav_html = """
<div class="bottom-nav">
  <button class="bottom-btn {home_active}" onclick="document.querySelector('button[kind=nav_home]')?.click()">🏠 Home</button>
  <button class="bottom-btn {fav_active}" onclick="document.querySelector('button[kind=nav_fav]')?.click()">❤️ Fav</button>
  <button class="bottom-btn {admin_active}" onclick="document.querySelector('button[kind=nav_admin]')?.click()">➕ Admin</button>
</div>
""".format(
    home_active="active" if st.session_state["active_tab"] == "home" else "",
    fav_active="active" if st.session_state["active_tab"] == "favorites" else "",
    admin_active="active" if st.session_state["active_tab"] == "admin" else "",
)
st.markdown(nav_html, unsafe_allow_html=True)

# Invisible helper buttons (JS clicks them) to change Streamlit session state
if st.button("nav_home", key="nav_home", help="nav home", on_click=lambda: set_tab("home")):
    pass
if st.button("nav_fav", key="nav_fav", help="nav fav", on_click=lambda: set_tab("favorites")):
    pass
if st.button("nav_admin", key="nav_admin", help="nav admin", on_click=lambda: set_tab("admin")):
    pass

# small helper to set tab (must be defined after the buttons)
def set_tab(tab_name):
    st.session_state["active_tab"] = tab_name
    # toggle admin sheet visibility
    st.session_state["show_admin_sheet"] = tab_name == "admin"
    st.session_state["selected_singer"] = None
    st.session_state["show_favorites"] = (tab_name == "favorites")
    st.session_state["playing_song"] = None
    st.experimental_rerun()


    verse_index = int(time.time() / 30) % len(BIBLE_VERSES)
    verse = BIBLE_VERSES[verse_index]
    st.markdown(
        f"""
        <div class='app-header'>
          <div style='display:flex; align-items:center; gap:10px;'>
            <img src="data:image/svg+xml;base64,{base64.b64encode(HEADER_SVG.encode()).decode()}" style="width:38px;height:38px;border-radius:10px;"/>
            <div class='app-title'>SoulFood</div>
          </div>
          <div class='verse-pill'>{verse}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# small inline SVG used for header icon (keeps external assets unchanged)
HEADER_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none'><rect width='24' height='24' rx='5' fill='#0b1220'/><path d='M9 9v6.5A3.5 3.5 0 1 0 15.5 19V8' stroke='url(#g)' stroke-width='1.2' stroke-linecap='round' stroke-linejoin='round'/><defs><linearGradient id='g' x1='0' x2='1'><stop offset='0' stop-color='#7dd3fc'/><stop offset='1' stop-color='#60a5fa'/></linearGradient></defs></svg>"""

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
        st.warning("⚠️ Playing file missing.")
        return

    data_url = audio_data_url(file_path)
    if not data_url:
        st.warning("⚠️ Cannot load audio for sticky player.")
        return

    player_html = f"""
    <div id="sticky-player" style="display:flex;">
      <div style="font-weight:800; min-width:140px; max-width:45%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
        🎧 {title}
      </div>
      <audio id="sticky-audio" controls style="flex:1; max-width:55%;">
        <source src="{data_url}" type="audio/mp3">
        Your browser does not support the audio element.
      </audio>
    </div>
    <script>
      const p = document.getElementById('sticky-player');
      if (p) p.style.display = 'flex';
    </script>
    """
    st.markdown(player_html, unsafe_allow_html=True)


# ---------------------- VIEWS (UI only changed) ----------------------
def show_singers():
    show_header()
    st.markdown(
        "<div style='margin-top:6px; font-weight:700; color:var(--muted); margin-bottom:6px;'>Choose a singer</div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="singer-grid">', unsafe_allow_html=True)
    for key, data in SINGERS.items():
        img_src = image_to_base64(data["image"]) if os.path.exists(data["image"]) else ""
        # Each singer card uses a button to open singer view (keeps old behavior)
        st.markdown(
            f"""
            <div class="singer-card" onclick="document.querySelector('button[kind=open_{key}]')?.click()">
                <img src="{img_src}" alt="{data['name']}">
                <div style="font-weight:800; margin-top:6px;">{data['name']}</div>
                <div style="margin-top:6px; color:var(--muted); font-weight:600; font-size:13px;">Tap to open</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Open {data['name']}", key=f"open_{key}"):
            st.session_state["selected_singer"] = key
            st.session_state["show_favorites"] = False
            st.session_state["playing_song"] = None
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def show_songs(singer_key):
    show_header()
    songs = get_songs_by_singer(singer_key)
    fav_ids = get_favorites()

    st.markdown(f"<div style='font-weight:800; font-size:18px; margin-bottom:6px;'>{SINGERS[singer_key]['name']}</div>", unsafe_allow_html=True)

    if st.button("⬅️ Back", key="back_top"):
        st.session_state["selected_singer"] = None
        st.session_state["playing_song"] = None
        st.session_state["show_favorites"] = False
        st.rerun()

    if not songs:
        st.info("No songs found for this singer.")
        return

    st.markdown('<div class="song-list">', unsafe_allow_html=True)

    for song_id, title, file_path in songs:
        fav_heart = "❤️" if song_id in fav_ids else "🤍"
        # Song tile
        st.markdown("<div class='song-tile'>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class='song-info'>
              <div class='song-title'>🎵 {title}</div>
              <div class='song-sub'>{SINGERS[singer_key]['name']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Buttons column (Play / Favorite / Delete)
        col_html = """
        <div style='display:flex; gap:8px; align-items:center;'>
        """
        st.markdown(col_html, unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.session_state.get("playing_song") == song_id:
                if st.button("⏸️", key=f"stop_{song_id}"):
                    st.session_state["playing_song"] = None
                    st.rerun()
            else:
                if st.button("▶️", key=f"play_{song_id}"):
                    st.session_state["playing_song"] = song_id
                    st.rerun()
        with c2:
            if st.button(fav_heart, key=f"fav_{song_id}"):
                toggle_favorite(song_id)
                st.rerun()
        with c3:
            if st.button("🗑️", key=f"del_{song_id}"):
                delete_song(song_id)

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def show_favorites_view():
    show_header()
    fav_ids = get_favorites()

    if not fav_ids:
        st.info("No favorites yet! Add some songs you love ❤️")
        return

    conn = get_conn()
    cur = conn.cursor()
    placeholders = ",".join(["?"] * len(fav_ids))
    cur.execute(f"SELECT id, title, file_path, singer FROM (SELECT id, title, file_path, singer FROM songs) WHERE id IN ({placeholders})", fav_ids)
    favs = cur.fetchall()
    conn.close()

    st.markdown("<div style='font-weight:800; font-size:18px; margin-bottom:6px;'>❤️ Favorites</div>", unsafe_allow_html=True)

    for song_id, title, file_path, _ in favs:
        st.markdown(
            f"<div class='song-tile'><div class='song-info'><div class='song-title'>🎵 {title}</div></div>",
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.session_state.get("playing_song") == song_id:
                if st.button("⏸️", key=f"stopfav_{song_id}"):
                    st.session_state["playing_song"] = None
                    st.rerun()
            else:
                if st.button("▶️", key=f"playfav_{song_id}"):
                    st.session_state["playing_song"] = song_id
                    st.rerun()
        with c2:
            if st.button("💔", key=f"remove_fav_{song_id}"):
                toggle_favorite(song_id)
                st.rerun()
            if st.button("🗑️", key=f"delete_fav_{song_id}"):
                delete_song(song_id)
        st.markdown("</div>", unsafe_allow_html=True)


# Admin view (same upload form & add singer flow as original, moved into main admin sheet)
def show_admin_sheet():
    st.markdown("<div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'><div style='font-weight:800; font-size:18px;'>➕ Admin</div><div style='color:var(--muted); font-weight:700;'>Upload & Manage</div></div>", unsafe_allow_html=True)
    with st.expander("➕ Add Singer (optional)", expanded=False):
        new_singer_key = st.text_input("Singer key (slug, e.g., john_doe)", key="admin_new_singer_key")
        new_singer_name = st.text_input("Singer name", key="admin_new_singer_name")
        new_singer_img = st.text_input("Image path (optional)", key="admin_new_singer_img")
        new_singer_folder = st.text_input("Folder path (optional, default audio/<key>)", key="admin_new_singer_folder")
        if st.button("Add Singer", key="admin_add_singer"):
            if not new_singer_key or not new_singer_name:
                st.error("Please provide both key and name.")
            else:
                key = new_singer_key.strip()
                folder = new_singer_folder.strip() or f"audio/{key}"
                SINGERS[key] = {"name": new_singer_name.strip(), "image": new_singer_img.strip() or "", "folder": folder}
                Path(folder).mkdir(parents=True, exist_ok=True)
                st.success(f"Added singer {new_singer_name}")
                st.experimental_rerun()

    st.markdown("---")
    with st.form("upload_form_main", clear_on_submit=True):
        singer_choice = st.selectbox("Select Singer", list(SINGERS.keys()), format_func=lambda x: SINGERS[x]["name"], key="admin_singer_choice")
        song_title = st.text_input("Song Title", key="admin_song_title")
        uploaded_file = st.file_uploader("Upload MP3 File", type=["mp3"], key="admin_upload")
        submitted = st.form_submit_button("Upload Song")
        if submitted:
            if not uploaded_file:
                st.error("⚠️ Please choose an MP3 file to upload.")
            elif not song_title:
                st.error("⚠️ Please enter the song title.")
            else:
                dest_folder = Path(SINGERS[singer_choice]["folder"])
                dest_folder.mkdir(parents=True, exist_ok=True)
                safe_name = uploaded_file.name.replace(" ", "_")
                dest_path = dest_folder / safe_name
                if dest_path.exists():
                    stem = dest_path.stem
                    suffix = dest_path.suffix
                    dest_path = dest_folder / f"{stem}_{int(time.time())}{suffix}"
                with open(dest_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                conn = get_conn()
                cur = conn.cursor()
                cur.execute("INSERT INTO songs (singer, title, file_path) VALUES (?, ?, ?)", (singer_choice, song_title, str(dest_path)))
                conn.commit()
                conn.close()
                st.success(f"✅ Song '{song_title}' uploaded successfully!")
                time.sleep(0.5)
                auto_sync_songs()
                st.experimental_rerun()


# ---------------------- APP START ------------------
create_tables()
auto_sync_songs()

if "selected_singer" not in st.session_state:
    st.session_state["selected_singer"] = None
if "show_favorites" not in st.session_state:
    st.session_state["show_favorites"] = False
if "playing_song" not in st.session_state:
    st.session_state["playing_song"] = None
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "home"
if "show_admin_sheet" not in st.session_state:
    st.session_state["show_admin_sheet"] = False

# Insert CSS
st.markdown(MOBILE_CSS, unsafe_allow_html=True)

# Main container (mobile-width)
st.markdown("<div class='block-container'>", unsafe_allow_html=True)

# Top header
show_header()

# Decide which main content to show (home / favorites / singer / admin)
if st.session_state["active_tab"] == "home" and not st.session_state["selected_singer"] and not st.session_state["show_favorites"]:
    show_singers()
elif st.session_state["active_tab"] == "favorites" or st.session_state.get("show_favorites"):
    st.session_state["active_tab"] = "favorites"
    st.session_state["show_favorites"] = True
    show_favorites_view()
elif st.session_state["selected_singer"]:
    show_songs(st.session_state["selected_singer"])
elif st.session_state["active_tab"] == "admin" or st.session_state.get("show_admin_sheet"):
    st.session_state["active_tab"] = "admin"
    show_admin_sheet()
else:
    show_singers()

st.markdown("</div>", unsafe_allow_html=True)

# Sticky bottom player
show_sticky_player_if_playing()

# Bottom navigation (native-like)
nav_html = """
<div class="bottom-nav">
  <button class="bottom-btn {home_active}" onclick="document.querySelector('button[kind=nav_home]')?.click()">🏠 Home</button>
  <button class="bottom-btn {fav_active}" onclick="document.querySelector('button[kind=nav_fav]')?.click()">❤️ Fav</button>
  <button class="bottom-btn {admin_active}" onclick="document.querySelector('button[kind=nav_admin]')?.click()">➕ Admin</button>
</div>
""".format(
    home_active="active" if st.session_state["active_tab"] == "home" else "",
    fav_active="active" if st.session_state["active_tab"] == "favorites" else "",
    admin_active="active" if st.session_state["active_tab"] == "admin" else "",
)
st.markdown(nav_html, unsafe_allow_html=True)

# Invisible helper buttons (JS clicks them) to change Streamlit session state
if st.button("nav_home", key="nav_home", help="nav home", on_click=lambda: set_tab("home")):
    pass
if st.button("nav_fav", key="nav_fav", help="nav fav", on_click=lambda: set_tab("favorites")):
    pass
if st.button("nav_admin", key="nav_admin", help="nav admin", on_click=lambda: set_tab("admin")):
    pass

# small helper to set tab (must be defined after the buttons)
def set_tab(tab_name):
    st.session_state["active_tab"] = tab_name
    # toggle admin sheet visibility
    st.session_state["show_admin_sheet"] = tab_name == "admin"
    st.session_state["selected_singer"] = None
    st.session_state["show_favorites"] = (tab_name == "favorites")
    st.session_state["playing_song"] = None
    st.experimental_rerun()
