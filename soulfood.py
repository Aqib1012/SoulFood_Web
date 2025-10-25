# soulfood_mobile.py
import streamlit as st
from pathlib import Path
import os
import sqlite3
import base64
import time
from streamlit_autorefresh import st_autorefresh

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="SoulFood 🎵", layout="wide", page_icon="🎶", initial_sidebar_state="collapsed")

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

PLACEHOLDER_IMG = "data:image/svg+xml;base64," + base64.b64encode(bytes(
    '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400"><rect width="100%" height="100%" fill="#e9eef8"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="#7b8aa5" font-size="22">No Image</text></svg>', "utf-8"
)).decode()

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
        return PLACEHOLDER_IMG


def get_songs_by_singer(singer_key):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, file_path FROM songs WHERE singer=? ORDER BY id DESC", (singer_key,))
    songs = cur.fetchall()
    conn.close()
    return songs


def get_all_songs():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, singer, title, file_path FROM songs ORDER BY id DESC")
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


# ---------------------- MOBILE STYLE CSS ------------------------
MOBILE_CSS = """
<style>
/* Reset for Streamlit content area to look like mobile */
.css-18e3th9 { padding: 0rem; } /* top-level container padding might vary by Streamlit version */
.css-1d391kg { padding-top: 0rem; } /* title area */
[data-testid="stAppViewContainer"] > .main { padding: 0px 0px !important; }

/* App background + container */
.app-shell {
    max-width: 480px;
    margin: 0 auto;
    background: linear-gradient(180deg, #f4f8ff 0%, #ffffff 100%);
    min-height: 100vh;
    position: relative;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    color: #0b1730;
}

/* Top header (small) */
.app-top {
    padding: 14px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid rgba(11,23,48,0.05);
    background: transparent;
}
.app-title {
    font-weight: 800;
    font-size: 18px;
    color: #0b63d4;
}

/* Verse */
.verse-box {
    margin: 12px;
    background: rgba(14,99,212,0.06);
    border-left: 4px solid #0b63d4;
    padding: 10px 12px;
    border-radius: 10px;
    font-style: italic;
    font-size: 14px;
}

/* Content area */
.content {
    padding: 12px;
    padding-bottom: 92px; /* space for bottom nav + sticky player */
}

/* Singer/ Song cards */
.card {
    background: white;
    border-radius: 14px;
    box-shadow: 0 10px 30px rgba(11,23,48,0.06);
    padding: 12px;
    margin-bottom: 12px;
    display: flex;
    gap: 12px;
    align-items: center;
}
.card .img {
    width: 68px;
    height: 68px;
    border-radius: 12px;
    object-fit: cover;
    flex-shrink: 0;
    border: 3px solid #e9f2ff;
}
.card .meta { flex: 1; min-width: 0; }
.title-small { font-weight:700; font-size:15px; margin-bottom:3px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}
.subtitle { font-size:13px; color:#6b7785; }

/* Buttons */
.btn-row { display:flex; gap:8px; margin-top:8px; }
.btn { padding:8px 12px; border-radius:10px; font-weight:600; border:none; cursor:pointer; min-width:80px; }
.btn-ghost { background: transparent; border: 1px solid rgba(11,23,48,0.06); }
.btn-primary { background: #0b63d4; color: #fff; }
.btn-fav { background: linear-gradient(90deg,#ff8fab,#ff6a9a); color: #fff; }

/* Bottom Navigation */
.bottom-nav {
    position: fixed;
    left: 50%;
    transform: translateX(-50%);
    bottom: 8px;
    width: 94%;
    max-width: 480px;
    background: white;
    border-radius: 14px;
    box-shadow: 0 12px 40px rgba(11,23,48,0.08);
    display: flex;
    justify-content: space-around;
    padding: 10px 8px;
    z-index: 9999;
}

/* Sticky player above bottom-nav */
.sticky-player {
    position: fixed;
    left: 50%;
    transform: translateX(-50%);
    bottom: 76px;
    width: 94%;
    max-width: 480px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 12px 40px rgba(11,23,48,0.08);
    padding: 10px;
    display: none; /* toggled visible by inline style from python */
    align-items: center;
    gap: 10px;
    z-index: 9998;
}

/* small player title */
.player-title { font-weight:700; font-size:14px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

/* Utility */
.center { text-align:center; }
.small-note { font-size:13px; color:#6b7785; margin-top:8px; text-align:center; }
</style>
"""

# ---------------------- HEADER / PLAYER HELPERS ----------------------
def render_top_header():
    st.markdown("<div class='app-top'>", unsafe_allow_html=True)
    st.markdown("<div style='display:flex; gap:10px; align-items:center;'><img src='https://raw.githubusercontent.com/github/explore/main/topics/music/music.png' width='34' style='border-radius:8px;'/><div class='app-title'>SoulFood</div></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size:13px; color:#6b7785;'>Mobile UI</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def show_verse():
    verse_index = int(time.time() / 30) % len(BIBLE_VERSES)
    verse = BIBLE_VERSES[verse_index]
    st.markdown(f"<div class='verse-box'>{verse}</div>", unsafe_allow_html=True)


def render_sticky_player():
    playing_id = st.session_state.get("playing_song")
    if not playing_id:
        # ensure hidden via CSS style
        st.markdown("<div class='sticky-player' id='sticky-player' style='display:none;'></div>", unsafe_allow_html=True)
        return

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT title, file_path FROM songs WHERE id=?", (playing_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        st.markdown("<div class='sticky-player' id='sticky-player' style='display:none;'></div>", unsafe_allow_html=True)
        return
    title, file_path = row
    data_url = audio_data_url(file_path)
    if not data_url:
        st.markdown("<div class='sticky-player' id='sticky-player' style='display:none;'></div>", unsafe_allow_html=True)
        st.warning("⚠️ Cannot load audio for sticky player.")
        return

    # Show player with full controls (seek supported)
    player_html = f"""
    <div class="sticky-player" id="sticky-player" style="display:flex;">
      <div style="flex:1; min-width:0;">
        <div class="player-title">🎧 {title}</div>
        <audio id="global-audio" controls style="width:100%; margin-top:6px;">
          <source src="{data_url}" type="audio/mp3">
          Your browser does not support audio.
        </audio>
      </div>
      <div style="width:10px;"></div>
    </div>
    <script>
      // Scroll sticky player into view on mobile when appear
      setTimeout(()=>{{ document.getElementById('sticky-player')?.scrollIntoView({{behavior:'smooth', block:'end'}}); }}, 80);
    </script>
    """
    st.markdown(player_html, unsafe_allow_html=True)


# ---------------------- VIEWS ----------------------
def view_home():
    st.markdown("<div class='content'>", unsafe_allow_html=True)
    show_verse()
    st.markdown("<h4 style='margin:12px 0 6px 6px;'>Artists</h4>", unsafe_allow_html=True)

    # Singer short list horizontally (we'll keep a vertical style for mobile)
    for key, data in SINGERS.items():
        img_src = image_to_base64(data["image"])
        st.markdown(
            f"""
            <div class='card' style='align-items:center;'>
                <img class='img' src='{img_src}'/>
                <div class='meta'>
                    <div class='title-small'>{data['name']}</div>
                    <div class='subtitle'>Tap to open songs</div>
                    <div style='margin-top:8px;'>
                        <button onclick="document.getElementById('open_{key}').click()" class='btn btn-primary'>Open</button>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open", key=f"open_{key}", args=None):
            st.session_state["page"] = "artist"
            st.session_state["selected_singer"] = key
            st.session_state["playing_song"] = None
            st.experimental_rerun()

    st.markdown("<h4 style='margin-top:8px;'>Recent Uploads</h4>", unsafe_allow_html=True)
    songs = get_all_songs()[:8]
    if not songs:
        st.markdown("<div class='small-note'>No songs uploaded yet. Use Upload tab to add songs.</div>", unsafe_allow_html=True)
    for song in songs:
        song_id, singer, title, file_path = song
        img_src = image_to_base64(SINGERS.get(singer, {}).get("image", ""))
        fav_ids = get_favorites()
        fav_heart = "❤️" if song_id in fav_ids else "🤍"
        data_url = audio_data_url(file_path) or ""
        st.markdown(
            f"""
            <div class='card'>
                <img class='img' src='{img_src}'/>
                <div class='meta'>
                    <div class='title-small'>{title}</div>
                    <div class='subtitle'>{SINGERS.get(singer,{{}}).get('name','')}</div>
                    <div class='btn-row'>
                        <form>
                          <button class='btn btn-primary' onclick="document.getElementById('play_{song_id}').click();return false;">Play</button>
                        </form>
                        <button class='btn btn-ghost' onclick="document.getElementById('fav_{song_id}').click();return false;">{fav_heart}</button>
                        <button class='btn btn-ghost' onclick="document.getElementById('del_{song_id}').click();return false;">Delete</button>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # hidden streamlit buttons to handle actions
        if st.button("Play", key=f"play_{song_id}", args=None):
            st.session_state["playing_song"] = song_id
            st.session_state["selected_singer"] = None
            st.session_state["page"] = "home"
            st.experimental_rerun()
        if st.button("Fav", key=f"fav_{song_id}", args=None):
            toggle_favorite(song_id)
            st.experimental_rerun()
        if st.button("Del", key=f"del_{song_id}", args=None):
            delete_song(song_id)

    st.markdown("</div>", unsafe_allow_html=True)


def view_artist(singer_key):
    st.markdown("<div class='content'>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='margin:6px 6px;'>🎤 {SINGERS[singer_key]['name']}</h3>", unsafe_allow_html=True)
    songs = get_songs_by_singer(singer_key)
    fav_ids = get_favorites()
    if not songs:
        st.markdown("<div class='small-note'>No songs found for this artist yet.</div>", unsafe_allow_html=True)
    for song_id, title, file_path in songs:
        fav_heart = "❤️" if song_id in fav_ids else "🤍"
        img_src = image_to_base64(SINGERS[singer_key]["image"])
        data_url = audio_data_url(file_path) or ""
        st.markdown(
            f"""
            <div class='card'>
                <img class='img' src='{img_src}'/>
                <div class='meta'>
                    <div class='title-small'>{title}</div>
                    <div class='subtitle'>{SINGERS[singer_key]['name']}</div>
                    <div class='btn-row'>
                        <button class='btn btn-primary' onclick="document.getElementById('play_{song_id}').click();return false;">Play</button>
                        <button class='btn btn-ghost' onclick="document.getElementById('fav_{song_id}').click();return false;">{fav_heart}</button>
                        <button class='btn btn-ghost' onclick="document.getElementById('del_{song_id}').click();return false;">Delete</button>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Play", key=f"play_{song_id}", args=None):
            st.session_state["playing_song"] = song_id
            st.experimental_rerun()
        if st.button("Fav", key=f"fav_{song_id}", args=None):
            toggle_favorite(song_id)
            st.experimental_rerun()
        if st.button("Del", key=f"del_{song_id}", args=None):
            delete_song(song_id)
    st.markdown("</div>", unsafe_allow_html=True)


def view_favorites():
    st.markdown("<div class='content'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin:6px;'>❤️ Favorites</h3>", unsafe_allow_html=True)
    fav_ids = get_favorites()
    if not fav_ids:
        st.markdown("<div class='small-note'>No favorites yet. Tap ❤️ on any song to add it here.</div>", unsafe_allow_html=True)
    else:
        conn = get_conn()
        cur = conn.cursor()
        placeholders = ",".join(["?"] * len(fav_ids))
        cur.execute(f"SELECT id, title, file_path, singer FROM songs WHERE id IN ({placeholders})", fav_ids)
        favs = cur.fetchall()
        conn.close()
        for row in favs:
            song_id, title, file_path, singer = row
            img_src = image_to_base64(SINGERS.get(singer, {}).get("image", ""))
            st.markdown(
                f"""
                <div class='card'>
                    <img class='img' src='{img_src}'/>
                    <div class='meta'>
                        <div class='title-small'>{title}</div>
                        <div class='subtitle'>{SINGERS.get(singer,{{}}).get('name','')}</div>
                        <div class='btn-row'>
                            <button class='btn btn-primary' onclick="document.getElementById('play_{song_id}').click();return false;">Play</button>
                            <button class='btn btn-ghost' onclick="document.getElementById('remove_{song_id}').click();return false;">Remove</button>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Play", key=f"play_{song_id}", args=None):
                st.session_state["playing_song"] = song_id
                st.experimental_rerun()
            if st.button("Remove", key=f"remove_{song_id}", args=None):
                toggle_favorite(song_id)
                st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def view_upload():
    st.markdown("<div class='content'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin:6px;'>➕ Upload Song</h3>", unsafe_allow_html=True)
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
                time.sleep(0.6)
                auto_sync_songs()
                st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def view_settings():
    st.markdown("<div class='content'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin:6px;'>⚙️ Settings</h3>", unsafe_allow_html=True)
    st.markdown("<div class='small-note'>Mobile-style Streamlit UI. Use Upload to add songs, Favorites to manage liked songs.</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:160px;'></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------- APP START ------------------
create_tables()
auto_sync_songs()

# session defaults
if "page" not in st.session_state:
    st.session_state["page"] = "home"
if "selected_singer" not in st.session_state:
    st.session_state["selected_singer"] = None
if "playing_song" not in st.session_state:
    st.session_state["playing_song"] = None

# load CSS
st.markdown(MOBILE_CSS, unsafe_allow_html=True)

# main app shell
st.markdown("<div class='app-shell'>", unsafe_allow_html=True)
render_top_header()

# small auto refresh for verse
st_autorefresh(interval=30000, key="verse_refresh")

# route pages
page = st.session_state["page"]
if page == "home":
    view_home()
elif page == "artist":
    key = st.session_state.get("selected_singer")
    if key:
        view_artist(key)
    else:
        st.session_state["page"] = "home"
        st.experimental_rerun()
elif page == "favorites":
    view_favorites()
elif page == "upload":
    view_upload()
elif page == "settings":
    view_settings()
else:
    view_home()

# sticky player
render_sticky_player()

# bottom navigation area (using streamlit buttons placed inside a fixed-bottom styled div)
bottom_nav_html = """
<div style="height:86px;"></div> <!-- spacer to allow scroll above fixed bottom -->
<div class='bottom-nav'>
  <div style='text-align:center; font-size:13px;'>
    <form><button class='btn btn-ghost' onclick="document.getElementById('nav_home').click();return false;">🏠<div style='font-size:11px;'>Home</div></button></form>
  </div>
  <div style='text-align:center; font-size:13px;'>
    <form><button class='btn btn-ghost' onclick="document.getElementById('nav_fav').click();return false;">❤️<div style='font-size:11px;'>Favs</div></button></form>
  </div>
  <div style='text-align:center; font-size:13px;'>
    <form><button class='btn btn-primary' onclick="document.getElementById('nav_upload').click();return false;">➕<div style='font-size:11px;'>Upload</div></button></form>
  </div>
  <div style='text-align:center; font-size:13px;'>
    <form><button class='btn btn-ghost' onclick="document.getElementById('nav_settings').click();return false;">⚙️<div style='font-size:11px;'>More</div></button></form>
  </div>
</div>
"""
st.markdown(bottom_nav_html, unsafe_allow_html=True)

# hidden streamlit buttons to catch bottom nav clicks
if st.button("nav_home", key="nav_home"):
    st.session_state["page"] = "home"
    st.session_state["selected_singer"] = None
    st.experimental_rerun()
if st.button("nav_fav", key="nav_fav"):
    st.session_state["page"] = "favorites"
    st.experimental_rerun()
if st.button("nav_upload", key="nav_upload"):
    st.session_state["page"] = "upload"
    st.experimental_rerun()
if st.button("nav_settings", key="nav_settings"):
    st.session_state["page"] = "settings"
    st.experimental_rerun()

st.markdown("</div>", unsafe_allow_html=True)

# end of file
