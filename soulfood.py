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
    st.experimental_rerun()


def audio_data_url(file_path):
    """Return a data URL for an mp3 file to use in an HTML audio tag (base64)."""
    try:
        with open(file_path, "rb") as f:
            b = f.read()
        b64 = base64.b64encode(b).decode()
        return f"data:audio/mp3;base64,{b64}"
    except Exception:
        return None


# ---------------------- CSS (MOBILE FIRST) ------------------------
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

/* Hide Streamlit default sidebar and tighten paddings */
section[data-testid="stSidebar"] { display: none !important; }
div.block-container { padding-left: 10px; padding-right: 10px; padding-top: 10px; }

body {
    background-color: var(--bg);
    color: var(--text);
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
}

/* Header */
.header { text-align: center; margin-top: 6px; margin-bottom: 6px; }
.title { color: var(--primary); font-weight: 800; margin-bottom: 4px; font-size:22px }
.verse-box { background-color: #e8f0fe; border-left: 5px solid var(--primary); border-radius: 10px; padding: 10px 12px; text-align: center; font-style: italic; color: var(--text); font-size: 14px; margin-top: 8px; }
.small-note { color: var(--muted); font-size:13px; margin-top:6px; text-align:center; }

/* Singer grid */
.singer-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-top: 12px; }
.singer-card { background-color: var(--card); border-radius: 14px; padding: 12px; text-align: center; box-shadow: 0 8px 22px var(--shadow); transition: all 0.18s ease; }
.singer-card:active { transform: scale(0.99); }
.singer-img { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; margin-bottom: 8px; border: 3px solid var(--primary); }

/* Song grid */
.song-grid { display: grid; gap: 12px; grid-template-columns: 1fr; margin-top: 12px; }
.song-card { background: var(--card); border-radius: 14px; padding: 12px; text-align: left; box-shadow: 0 8px 22px var(--shadow); transition: transform .16s ease; }
.song-card:active { transform: scale(0.995); }
.song-card h4 { margin: 6px 0 10px 0; font-size:16px }

.controls-row { display:flex; gap:8px; justify-content:flex-start; flex-wrap:wrap; margin-top:8px; }
.btn { padding:8px 10px; border-radius:10px; font-weight:600; border:none; cursor:pointer; }
.btn-ghost { background: transparent; border: 1px solid rgba(0,0,0,0.06); }
.btn-primary { background: var(--primary); color: #fff; }

/* Sticky mini player */
#sticky-player { position: fixed; bottom: 70px; left: 10px; right: 10px; background: var(--card); border-radius: 14px; padding: 8px 10px; box-shadow: 0 10px 40px var(--shadow); display: none; align-items: center; justify-content: center; z-index: 9998; }

/* Bottom navigation */
.bottom-nav { position: fixed; bottom: 8px; left: 8px; right: 8px; height: 56px; background: white; display: flex; justify-content: space-around; align-items: center; box-shadow: 0 -6px 20px rgba(2,6,23,0.06); border-radius: 12px; z-index: 9999; }
.bottom-nav button { background: none; border: none; font-size: 20px; cursor: pointer; }

@media(min-width:900px) {
  .song-grid { grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
  .singer-row { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
  #sticky-player { bottom: 90px; left: 15%; right: 15%; }
}

</style>
"""

# ---------------------- HEADER / PLAYER HELPERS ----------------------

def show_header():
    # Auto refresh every 30s for verse
    st_autorefresh(interval=30000, key="verse_refresh")
    st.markdown("<div class='header'>", unsafe_allow_html=True)
    st.markdown("<h1 class='title'>🎵 SoulFood – پرستش 🎵</h1>", unsafe_allow_html=True)
    st.markdown("<p class='small-note'>Gospel Music Player — Mobile & Desktop friendly</p>", unsafe_allow_html=True)
    verse_index = int(time.time() / 30) % len(BIBLE_VERSES)
    verse = BIBLE_VERSES[verse_index]
    st.markdown(f"<div class='verse-box'>{verse}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---", unsafe_allow_html=True)


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

    # Render a minimal HTML audio player fixed at bottom with controls & title
    player_html = f"""
    <div id="sticky-player" style="display:flex; gap:12px; align-items:center; justify-content:space-between;">
      <div style="font-weight:700; min-width:120px; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">
        🎧 {title}
      </div>
      <audio id="sticky-audio" controls style="max-width:58%; width:58%;">
        <source src="{data_url}" type="audio/mp3">
        Your browser does not support the audio element.
      </audio>
      <div style="min-width:80px; display:flex; gap:6px; justify-content:center;">
        <button onclick="document.getElementById('sticky-audio').pause();" style="padding:8px;border-radius:8px;">⏸️</button>
        <button onclick="document.getElementById('sticky-audio').play();" style="padding:8px;border-radius:8px;">▶️</button>
      </div>
    </div>
    <script>
      const p = document.getElementById('sticky-player');
      if (p) p.style.display = 'flex';
    </script>
    """
    st.markdown(player_html, unsafe_allow_html=True)


# ---------------------- VIEWS ----------------------

def show_singers():
    show_header()
    st.info("📱 Tap a singer to open their songs. Use the bottom bar for navigation.")
    st.markdown("<h3 style='text-align:center; margin-top:6px;'>Select a Singer</h3>", unsafe_allow_html=True)
    st.markdown('<div class="singer-row">', unsafe_allow_html=True)

    for key, data in SINGERS.items():
        img_src = image_to_base64(data["image"]) if os.path.exists(data["image"]) else ""
        st.markdown(
            f"""
            <div class="singer-card">
                <img src="{img_src}" class="singer-img" alt="{data['name']}">
                <h4 style="margin-bottom:6px;">{data['name']}</h4>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Each singer rendered with a button under it
        if st.button(f"Open {data['name']}", key=f"open_{key}"):
            st.session_state["selected_singer"] = key
            st.session_state["show_favorites"] = False
            st.session_state["playing_song"] = None
            st.experimental_rerun()

    st.markdown('</div>', unsafe_allow_html=True)


def show_songs(singer_key):
    show_header()
    songs = get_songs_by_singer(singer_key)
    fav_ids = get_favorites()

    st.markdown(f"<h3 style='text-align:center; margin-top:6px;'>{SINGERS[singer_key]['name']} Songs</h3>", unsafe_allow_html=True)

    if st.button("⬅️ Back", key="back_top"):
        st.session_state["selected_singer"] = None
        st.session_state["playing_song"] = None
        st.session_state["show_favorites"] = False
        st.experimental_rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if not songs:
        st.info("No songs found for this singer.")
        return

    st.markdown('<div class="song-grid">', unsafe_allow_html=True)

    for song_id, title, file_path in songs:
        fav_heart = "❤️" if song_id in fav_ids else "🤍"
        st.markdown("<div class='song-card'>", unsafe_allow_html=True)
        st.markdown(f"<h4>🎵 {title}</h4>", unsafe_allow_html=True)

        # Show inline audio player only when playing this song (so grid stays small)
        if st.session_state.get("playing_song") == song_id:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "rb") as f:
                        st.audio(f.read(), format="audio/mp3")
                except Exception:
                    st.warning("⚠️ Failed to load audio file.")
            else:
                st.warning("⚠️ Audio file missing!")

        # Buttons in a row
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.session_state.get("playing_song") == song_id:
                if st.button("⏸️ Stop", key=f"stop_{song_id}"):
                    st.session_state["playing_song"] = None
                    st.experimental_rerun()
            else:
                if st.button("▶️ Play", key=f"play_{song_id}"):
                    st.session_state["playing_song"] = song_id
                    st.experimental_rerun()

        with c2:
            if st.button(fav_heart + " Favorite", key=f"fav_{song_id}"):
                toggle_favorite(song_id)
                st.experimental_rerun()

        with c3:
            if st.button("🗑️ Delete", key=f"del_{song_id}"):
                delete_song(song_id)

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


def show_favorites_view():
    show_header()
    fav_ids = get_favorites()

    if not fav_ids:
        st.info("No favorites yet! Add some songs you love ❤️")
        return

    conn = get_conn()
    cur = conn.cursor()
    placeholders = ",".join(["?"] * len(fav_ids))
    cur.execute(f"SELECT id, title, file_path FROM songs WHERE id IN ({placeholders})", fav_ids)
    favs = cur.fetchall()
    conn.close()

    st.markdown("<h3 style='text-align:center; margin-top:6px;'>❤️ Your Favorite Songs</h3>", unsafe_allow_html=True)

    if st.button("⬅️ Back", key="back_from_fav"):
        st.session_state["show_favorites"] = False
        st.session_state["selected_singer"] = None
        st.session_state["playing_song"] = None
        st.experimental_rerun()

    for song_id, title, file_path in favs:
        st.markdown(
            f"<div style='text-align:center; background:var(--card); padding:12px; border-radius:12px; box-shadow: 0 8px 20px var(--shadow); margin-bottom:12px;'>"
            f"<h4>🎵 {title}</h4>",
            unsafe_allow_html=True,
        )

        if st.session_state.get("playing_song") == song_id:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "rb") as f:
                        st.audio(f.read(), format="audio/mp3")
                except Exception:
                    st.warning("⚠️ Failed to load audio file.")
            else:
                st.warning("⚠️ Audio file missing!")

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.session_state.get("playing_song") == song_id:
                if st.button("⏸️ Stop", key=f"stopfav_{song_id}"):
                    st.session_state["playing_song"] = None
                    st.experimental_rerun()
            else:
                if st.button("▶️ Play", key=f"playfav_{song_id}"):
                    st.session_state["playing_song"] = song_id
                    st.experimental_rerun()
        with c2:
            if st.button("💔 Remove", key=f"remove_fav_{song_id}"):
                toggle_favorite(song_id)
                st.experimental_rerun()
            if st.button("🗑️ Delete", key=f"delete_fav_{song_id}"):
                delete_song(song_id)
        st.markdown("</div>", unsafe_allow_html=True)


def show_upload_page():
    show_header()
    st.markdown("<h3 style='text-align:center; margin-top:6px;'>⬆️ Upload New Song</h3>", unsafe_allow_html=True)
    with st.form("upload_form_main", clear_on_submit=True):
        singer_choice = st.selectbox("Select Singer", list(SINGERS.keys()), format_func=lambda x: SINGERS[x]["name"])
        song_title = st.text_input("Song Title")
        uploaded_file = st.file_uploader("Upload MP3 File", type=["mp3"])
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
if "view" not in st.session_state:
    st.session_state["view"] = "home"

# Insert base CSS
st.markdown(BASE_CSS, unsafe_allow_html=True)

# Top-level navigation (buttons)
nav_cols = st.columns([1, 1, 1])
with nav_cols[0]:
    if st.button("🏠 Home"):
        st.session_state["view"] = "home"
        st.session_state["selected_singer"] = None
        st.session_state["show_favorites"] = False
        st.session_state["playing_song"] = None
        st.experimental_rerun()
with nav_cols[1]:
    if st.button("❤️ Favorites"):
        st.session_state["view"] = "favorites"
        st.session_state["show_favorites"] = True
        st.session_state["selected_singer"] = None
        st.session_state["playing_song"] = None
        st.experimental_rerun()
with nav_cols[2]:
    if st.button("⬆️ Upload"):
        st.session_state["view"] = "upload"
        st.session_state["selected_singer"] = None
        st.session_state["show_favorites"] = False
        st.session_state["playing_song"] = None
        st.experimental_rerun()

# Main routing
if st.session_state["view"] == "home":
    # If a singer was selected via button, show songs
    if st.session_state["selected_singer"]:
        show_songs(st.session_state["selected_singer"])
    else:
        show_singers()
elif st.session_state["view"] == "favorites":
    show_favorites_view()
elif st.session_state["view"] == "upload":
    show_upload_page()
else:
    show_singers()

# bottom nav (html) - purely cosmetic and duplicates top nav
# ---------------------- BOTTOM NAVIGATION ----------------------
nav_placeholder = st.empty()

with nav_placeholder.container():
    st.markdown("""
    <style>
    .bottom-nav {
        position: fixed;
        bottom: 8px;
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
    """, unsafe_allow_html=True)

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


# sticky bottom player area (rendered regardless; its internal JS toggles display)
show_sticky_player_if_playing()
