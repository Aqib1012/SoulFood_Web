import streamlit as st
from pathlib import Path
import os
import sqlite3
import base64
import time
from streamlit_autorefresh import st_autorefresh

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="SoulFood 🎵", layout="wide", page_icon="🎶")

# ---------------------- DATABASE -------------------
DB_PATH = "database.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


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
        # detect extension from file name
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
    if file_path_row and os.path.exists(file_path_row[0]):
        try:
            os.remove(file_path_row[0])
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


# ---------------------- CSS (LIGHT + DARK + RESPONSIVE) ------------------------
BASE_CSS = """
<style>
:root {
  --bg: #f6f9fc;
  --card: #ffffff;
  --muted: #5b6876;
  --primary: #007BFF;
  --text: #0b1730;
  --accent: #0b63d4;
  --shadow: rgba(2,6,23,0.06);
}

/* Dark overrides will be injected if dark mode is selected */

body {
    background-color: var(--bg);
    color: var(--text);
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
}

/* Header */
.header {
    text-align: center;
    margin-top: 8px;
    margin-bottom: 6px;
}
.title {
    color: var(--primary);
    font-weight: 800;
    margin-bottom: 4px;
}

/* Verse box */
.verse-box {
    background-color: #e8f0fe;
    border-left: 5px solid var(--primary);
    border-radius: 10px;
    padding: 10px 15px;
    text-align: center;
    font-style: italic;
    color: var(--text);
    font-size: 16px;
    margin-top: 8px;
    animation: fadeIn 1s ease-in-out;
}

/* Singer grid */
.singer-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 22px;
    margin-top: 20px;
    width: 100%;
    max-width: 1100px;
    margin-left: auto;
    margin-right: auto;
    padding: 6px;
}

.singer-card {
    background-color: var(--card);
    border-radius: 14px;
    padding: 18px;
    text-align: center;
    box-shadow: 0 8px 22px var(--shadow);
    transition: all 0.28s ease;
}
.singer-card:hover {
    transform: translateY(-6px);
}

/* Singer image circle */
.singer-img {
    width: 140px;
    height: 140px;
    border-radius: 50%;
    object-fit: cover;
    margin-bottom: 12px;
    border: 4px solid var(--primary);
}

/* Song grid */
.song-grid {
    display: grid;
    gap: 20px;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    width: 100%;
    max-width: 1100px;
    margin-left: auto;
    margin-right: auto;
    padding: 6px;
}

.song-card {
    background: var(--card);
    border-radius: 12px;
    padding: 14px;
    text-align: center;
    box-shadow: 0 8px 22px var(--shadow);
    transition: transform .22s ease, box-shadow .22s ease;
}
.song-card:hover { transform: translateY(-6px); box-shadow: 0 12px 36px var(--shadow); }
.song-card h4 { margin: 8px 0 10px 0; }

/* Buttons layout */
.controls-row { display:flex; gap:10px; justify-content:center; flex-wrap:wrap; margin-top:8px; }
.btn { padding:10px 12px; border-radius:10px; font-weight:600; border:none; cursor:pointer; }
.btn-ghost { background: transparent; border: 1px solid rgba(0,0,0,0.06); }
.btn-primary { background: var(--primary); color: #fff; }

/* Sidebar responsive: when screen small, sidebar becomes full width */
@media (max-width: 700px) {
    section[data-testid="stSidebar"] { position: relative !important; width: 100% !important; min-width: unset !important; z-index:9999; }
    .singer-img { width: 120px; height:120px; }
}

/* Sticky bottom player */
#sticky-player {
    position: fixed;
    left: 15%;
    right: 15%;
    bottom: 18px;
    background: var(--card);
    border-radius: 14px;
    padding: 10px 14px;
    box-shadow: 0 10px 40px var(--shadow);
    display: none; /* toggled visible by JS/CSS when playing */
    align-items: center;
    justify-content: center;
    z-index: 9998;
}

/* If viewport small, make player full width bottom */
@media (max-width: 900px) {
    #sticky-player { left: 8px; right: 8px; }
}

/* simple fade animation */
@keyframes fadeIn { from { opacity: 0;} to { opacity: 1; } }

.small-note { color: var(--muted); font-size:13px; margin-top:6px; text-align:center; }

</style>
"""

# ---------------------- DARK THEME CSS -------------------
# ---- Pure DARK MODE CSS ----
dark_css = """
<style>
    /* Full App Background */
    .stApp {
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0d0d0d !important;
        color: #FFFFFF !important;
    }

    /* Buttons */
    button[kind="primary"] {
        background-color: #1a1a1a !important;
        color: white !important;
        border: 1px solid #333 !important;
    }

    button:hover {
        background-color: #333333 !important;
        color: white !important;
    }

    /* Text Inputs */
    .stTextInput > div > div > input {
        background-color: #1a1a1a !important;
        color: white !important;
    }

    /* Audio Player Background */
    audio {
        filter: invert(1) hue-rotate(180deg);
    }
</style>
"""
st.markdown(dark_css, unsafe_allow_html=True)


# ---------------------- HEADER / PLAYER HELPERS ---------------------
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
        # hide player by ensuring the element isn't rendered
        return

    # lookup file_path and title
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
    <div id="sticky-player" style="display:flex; gap:12px; align-items:center; justify-content:center;">
      <div style="font-weight:700; min-width:180px; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;">
        🎧 {title}
      </div>
      <audio id="sticky-audio" controls style="max-width:70%; width:100%;">
        <source src="{data_url}" type="audio/mp3">
        Your browser does not support the audio element.
      </audio>
      <div style="min-width:80px; display:flex; gap:6px; justify-content:center;">
        <button onclick="document.getElementById('sticky-audio').pause();" style="padding:8px;border-radius:8px;">⏸️</button>
        <button onclick="document.getElementById('sticky-audio').play();" style="padding:8px;border-radius:8px;">▶️</button>
      </div>
    </div>
    <script>
      // make the sticky player visible
      const p = document.getElementById('sticky-player');
      if (p) p.style.display = 'flex';
      // ensure audio stops when session state playing_song becomes null (user actions still needed)
    </script>
    """
    st.markdown(player_html, unsafe_allow_html=True)


# ---------------------- VIEWS ----------------------
def show_singers():
    show_header()
    st.info(
        """
        📱 **Mobile tip:** Tap the top-left menu (≡) for the Admin Panel.  
        Use the buttons under each singer to open their songs.
        """,
        icon="ℹ️",
    )
    st.markdown("<h3 style='text-align:center; margin-top:6px;'>Select a Singer</h3>", unsafe_allow_html=True)
    st.markdown('<div class="singer-row">', unsafe_allow_html=True)

    for key, data in SINGERS.items():
        img_src = image_to_base64(data["image"]) if os.path.exists(data["image"]) else ""
        # Render singer card (image + button)
        st.markdown(
            f"""
            <div class="singer-card">
                <img src="{img_src}" class="singer-img" alt="{data['name']}">
                <h4 style="margin-bottom:6px;">{data['name']}</h4>
                <div style="margin-top:8px;">
                    <button onclick="document.querySelector('button[kind=play_{key}]')?.click()" class="btn btn-primary">🎤 Listen</button>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # separate Streamlit button that actually triggers selection
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

    st.markdown(f"<h3 style='text-align:center; margin-top:6px;'>{SINGERS[singer_key]['name']} Songs</h3>", unsafe_allow_html=True)

    if st.button("⬅️ Back to Singers", key="back_top"):
        st.session_state["selected_singer"] = None
        st.session_state["playing_song"] = None
        st.session_state["show_favorites"] = False
        st.rerun()

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
                    st.rerun()
            else:
                if st.button("▶️ Play", key=f"play_{song_id}"):
                    st.session_state["playing_song"] = song_id
                    st.rerun()

        with c2:
            if st.button(fav_heart + " Favorite", key=f"fav_{song_id}"):
                toggle_favorite(song_id)
                st.rerun()

        with c3:
            if st.button("🗑️ Delete", key=f"del_{song_id}"):
                delete_song(song_id)

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
    cur.execute(f"SELECT id, title, file_path FROM songs WHERE id IN ({placeholders})", fav_ids)
    favs = cur.fetchall()
    conn.close()

    st.markdown("<h3 style='text-align:center; margin-top:6px;'>❤️ Your Favorite Songs</h3>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Singers"):
        st.session_state["show_favorites"] = False
        st.session_state["selected_singer"] = None
        st.session_state["playing_song"] = None
        st.rerun()

    for song_id, title, file_path in favs:
        st.markdown(
            f"<div style='text-align:center; background:var(--card); padding:15px; border-radius:12px; "
            f"box-shadow: 0 8px 20px var(--shadow); margin-bottom:16px;'>"
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
                    st.rerun()
            else:
                if st.button("▶️ Play", key=f"playfav_{song_id}"):
                    st.session_state["playing_song"] = song_id
                    st.rerun()
        with c2:
            if st.button("💔 Remove", key=f"remove_fav_{song_id}"):
                toggle_favorite(song_id)
                st.rerun()
            if st.button("🗑️ Delete", key=f"delete_fav_{song_id}"):
                delete_song(song_id)
        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------- APP START ------------------
create_tables()
auto_sync_songs()

if "selected_singer" not in st.session_state:
    st.session_state["selected_singer"] = None
if "show_favorites" not in st.session_state:
    st.session_state["show_favorites"] = False
if "playing_song" not in st.session_state:
    st.session_state["playing_song"] = None
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False

# Insert base CSS
st.markdown(BASE_CSS, unsafe_allow_html=True)
# Conditionally insert dark css
if st.session_state["dark_mode"]:
    st.markdown(DARK_CSS, unsafe_allow_html=True)

# ---------------------- SIDEBAR (responsive + dark toggle + upload) --------------------
with st.sidebar:
    st.markdown("<div style='text-align:center; margin-bottom:8px;'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:var(--primary);'>🎧 Admin Panel – Add New Song</h4>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Dark mode toggle
    dm = st.checkbox("🌙 Dark Mode", value=st.session_state["dark_mode"], key="dm_toggle")
    if dm != st.session_state["dark_mode"]:
        st.session_state["dark_mode"] = dm
        # refresh page to apply theme css
        st.rerun()

    # Add new singer (optional small form)
    with st.expander("➕ Add Singer (optional)", expanded=False):
        new_singer_key = st.text_input("Singer key (slug, e.g., john_doe)")
        new_singer_name = st.text_input("Singer name")
        new_singer_img = st.text_input("Image path (optional)")
        new_singer_folder = st.text_input("Folder path (optional, default audio/<key>)")
        if st.button("Add Singer"):
            if not new_singer_key or not new_singer_name:
                st.error("Please provide both key and name.")
            else:
                key = new_singer_key.strip()
                folder = new_singer_folder.strip() or f"audio/{key}"
                SINGERS[key] = {"name": new_singer_name.strip(), "image": new_singer_img.strip() or "", "folder": folder}
                Path(folder).mkdir(parents=True, exist_ok=True)
                st.success(f"Added singer {new_singer_name}")
                st.rerun()

    st.markdown("---")

    # Upload form
    with st.form("upload_form", clear_on_submit=True):
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
                time.sleep(1.0)
                auto_sync_songs()
                st.rerun()

    st.markdown("---")
    if st.button("❤️ View Favorites"):
        st.session_state["show_favorites"] = True
        st.session_state["selected_singer"] = None
        st.session_state["playing_song"] = None
        st.rerun()

# ---------------------- MAIN VIEW ------------------
if st.session_state["show_favorites"]:
    show_favorites_view()
elif st.session_state["selected_singer"]:
    show_songs(st.session_state["selected_singer"])
else:
    show_singers()

# sticky bottom player area (rendered regardless; its internal JS toggles display)
show_sticky_player_if_playing()
