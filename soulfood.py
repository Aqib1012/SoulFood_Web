import streamlit as st
from pathlib import Path
import os
import sqlite3
import base64
import time

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="SoulFood 🎵", layout="wide", page_icon="🎶")

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

# ---------------------- CSS (MOBILE APP STYLE) ------------------------
BASE_CSS = """
<style>
:root{
  --bg: #0f1724;
  --card: #0b1220;
  --muted: #9aa4b2;
  --primary: linear-gradient(90deg,#3b82f6,#06b6d4);
  --accent: #06b6d4;
  --text: #e6eef8;
  --soft: rgba(255,255,255,0.03);
  --glass: rgba(255,255,255,0.02);
}

/* page background */
body {
  background: radial-gradient(circle at 10% 10%, rgba(99,102,241,0.08), transparent 20%),
              radial-gradient(circle at 90% 90%, rgba(6,182,212,0.03), transparent 20%),
              var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
}

/* header */
.header {
  text-align: center;
  padding-top: 10px;
  padding-bottom: 6px;
}
.title {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.2px;
  margin-bottom: 2px;
}
.subtitle { color: var(--muted); font-size:12px; margin-top:2px; }

/* container card look */
.container {
  max-width: 980px;
  margin-left: auto;
  margin-right: auto;
  padding: 12px;
}

/* singer grid - mobile friendly */
.singer-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 14px;
    margin-top: 16px;
}

.singer-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    border-radius: 14px;
    padding: 12px;
    text-align: center;
    box-shadow: 0 6px 20px rgba(2,6,23,0.5);
    transition: transform .18s ease, box-shadow .18s ease;
    border: 1px solid rgba(255,255,255,0.03);
}
.singer-card:hover { transform: translateY(-6px); }

/* images */
.singer-img {
    width: 92px;
    height: 92px;
    border-radius: 50%;
    object-fit: cover;
    margin: 0 auto 8px;
    border: 3px solid rgba(255,255,255,0.04);
}

/* song grid */
.song-grid {
    display: grid;
    gap: 12px;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    margin-top: 10px;
}
.song-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    border-radius: 12px;
    padding: 12px;
    box-shadow: 0 8px 24px rgba(2,6,23,0.5);
    border: 1px solid rgba(255,255,255,0.03);
}
.song-card h4 { margin: 6px 0 10px 0; font-size:16px; color:var(--text); }

/* controls */
.controls-row { display:flex; gap:8px; justify-content:center; align-items:center; flex-wrap:wrap; margin-top:8px; }
.btn {
  padding:8px 12px;
  border-radius:10px;
  font-weight:700;
  border: none;
  cursor: pointer;
  background: rgba(255,255,255,0.02);
  color: var(--text);
}
.btn-primary {
  background: linear-gradient(90deg,#3b82f6,#06b6d4);
  color: white;
  box-shadow: 0 8px 24px rgba(6,182,212,0.08);
}

/* bottom navigation */
.bottom-nav {
  position: fixed;
  left: 8px;
  right: 8px;
  bottom: 72px;
  background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
  border-radius: 14px;
  padding: 8px 10px;
  display: flex;
  justify-content: space-around;
  align-items: center;
  box-shadow: 0 12px 40px rgba(2,6,23,0.55);
  border: 1px solid rgba(255,255,255,0.03);
  z-index: 9996;
}

/* sticky player */
#sticky-player {
    position: fixed;
    left: 8px;
    right: 8px;
    bottom: 8px;
    background: linear-gradient(90deg, rgba(11,17,32,0.9), rgba(6,25,40,0.9));
    border-radius: 14px;
    padding: 10px 12px;
    box-shadow: 0 14px 50px rgba(2,6,23,0.6);
    display: none;
    align-items: center;
    justify-content: space-between;
    z-index: 9999;
    border: 1px solid rgba(255,255,255,0.04);
}
.player-left { display:flex; gap:12px; align-items:center; min-width: 40%; }
.player-title { font-weight:700; overflow:hidden; white-space:nowrap; text-overflow:ellipsis; max-width:220px; }
.player-controls { display:flex; gap:6px; align-items:center; justify-content:center; }

/* responsive tweaks */
@media (max-width: 700px) {
  .container { padding-left: 10px; padding-right: 10px; }
  .singer-img { width:86px; height:86px; }
  .bottom-nav { left: 6px; right: 6px; bottom: 84px; }
  #sticky-player { left: 6px; right: 6px; bottom: 6px; }
}

.small-note { color: var(--muted); font-size:12px; margin-top:6px; text-align:center; }
</style>
"""

# ---------------------- HEADER / PLAYER HELPERS ----------------------
def show_header():
    st.markdown("<div class='header'>", unsafe_allow_html=True)
    st.markdown("<div class='title'>🎵 SoulFood – پرستش</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Gospel Music — Mobile friendly</div>", unsafe_allow_html=True)
    verse_index = int(time.time() / 45) % len(BIBLE_VERSES)
    verse = BIBLE_VERSES[verse_index]
    st.markdown(f"<div style='margin-top:8px; padding:8px; border-radius:10px; text-align:center; background:rgba(255,255,255,0.01);'>{verse}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

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

    # sticky player HTML
    player_html = f"""
    <div id="sticky-player" style="display:flex;">
      <div class="player-left">
        <img src="" style="width:54px;height:54px;border-radius:8px;background:rgba(255,255,255,0.02)">
        <div style="display:flex;flex-direction:column;">
          <div class="player-title">🎧 {title}</div>
          <div style="font-size:12px;color:rgba(255,255,255,0.6);">Now playing</div>
        </div>
      </div>
      <div style="flex:1; display:flex; justify-content:center; align-items:center;">
        <div class="player-controls">
          <button onclick="document.getElementById('sticky-audio').currentTime -= 10;" class="btn">⏪</button>
          <button onclick="document.getElementById('sticky-audio').play();" class="btn btn-primary">▶️</button>
          <button onclick="document.getElementById('sticky-audio').pause();" class="btn">⏸️</button>
          <button onclick="document.getElementById('sticky-audio').currentTime += 10;" class="btn">⏩</button>
        </div>
      </div>
      <audio id="sticky-audio" preload="none" style="display:none;">
        <source src="{data_url}" type="audio/mp3">
      </audio>
    </div>
    """
    st.markdown(player_html, unsafe_allow_html=True)

# ---------------------- VIEWS ----------------------
def home_view():
    show_header()
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top:10px;'>Select a Singer</h3>", unsafe_allow_html=True)
    st.markdown('<div class="singer-row">', unsafe_allow_html=True)

    for key, data in SINGERS.items():
        img_src = image_to_base64(data["image"]) if os.path.exists(data["image"]) else ""
        card_html = f"""
        <div class="singer-card">
            <img src="{img_src}" class="singer-img" alt="{data['name']}">
            <div style="font-weight:700; margin-top:6px;">{data['name']}</div>
            <div style="margin-top:8px;">
                <button onclick="window._st_click_open('{key}')" class="btn btn-primary" style="margin-top:8px;">🎤 Open</button>
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)

    # JS hook buttons (fake) — we'll capture clicks via custom components alternative:
    # Because direct onclick can't call Python, we provide real streamlit buttons below (hidden in layout)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Provide lightweight grid of actual buttons to interact (hidden on wide screens)
    cols = st.columns(len(SINGERS))
    i = 0
    for key, data in SINGERS.items():
        with cols[i]:
            if st.button(f"Open {data['name']}", key=f"open_btn_{key}"):
                st.session_state["page"] = "songs"
                st.session_state["selected_singer"] = key
                st.session_state["playing_song"] = None
                st.experimental_rerun()
        i += 1

def songs_view(singer_key):
    show_header()
    songs = get_songs_by_singer(singer_key)
    fav_ids = get_favorites()

    st.markdown("<div class='container'>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='margin-top:10px;'>{SINGERS[singer_key]['name']} — Songs</h3>", unsafe_allow_html=True)

    if st.button("⬅️ Back", key="back_top"):
        st.session_state["page"] = "home"
        st.session_state["selected_singer"] = None
        st.session_state["playing_song"] = None
        st.experimental_rerun()

    if not songs:
        st.info("No songs found for this singer.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.markdown('<div class="song-grid">', unsafe_allow_html=True)
    for song_id, title, file_path in songs:
        fav_heart = "❤️" if song_id in fav_ids else "🤍"
        st.markdown("<div class='song-card'>", unsafe_allow_html=True)
        st.markdown(f"<h4>🎵 {title}</h4>", unsafe_allow_html=True)

        # show small player inline (toggle)
        if st.session_state.get("playing_song") == song_id:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "rb") as f:
                        st.audio(f.read(), format="audio/mp3")
                except Exception:
                    st.warning("⚠️ Failed to load audio file.")
            else:
                st.warning("⚠️ Audio file missing!")

        c1, c2, c3 = st.columns([1,1,1])
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

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def favorites_view():
    show_header()
    fav_ids = get_favorites()
    st.markdown("<div class='container'>", unsafe_allow_html=True)

    st.markdown("<h3 style='margin-top:10px;'>❤️ Favorites</h3>", unsafe_allow_html=True)
    if not fav_ids:
        st.info("No favorites yet! Add some songs you love ❤️")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    conn = get_conn()
    cur = conn.cursor()
    placeholders = ",".join(["?"] * len(fav_ids))
    cur.execute(f"SELECT id, title, file_path FROM songs WHERE id IN ({placeholders})", fav_ids)
    favs = cur.fetchall()
    conn.close()

    for song_id, title, file_path in favs:
        st.markdown(
            f"<div style='text-align:left; background:linear-gradient(180deg, rgba(255,255,255,0.01), rgba(255,255,255,0.00)); padding:12px; border-radius:10px; margin-bottom:10px;'>"
            f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
            f"<div style='font-weight:700;'>🎵 {title}</div>"
            f"<div style='font-size:12px; color:rgba(255,255,255,0.6);'>Favorite</div>"
            f"</div>",
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

        c1, c2 = st.columns([1,1])
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

    st.markdown("</div>", unsafe_allow_html=True)

def admin_view():
    show_header()
    st.markdown("<div class='container'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top:10px;'>⚙️ Admin — Add / Upload</h3>", unsafe_allow_html=True)

    with st.expander("➕ Add Singer (optional)", expanded=False):
        new_singer_key = st.text_input("Singer key (slug, e.g., john_doe)")
        new_singer_name = st.text_input("Singer name")
        new_singer_img = st.text_input("Image path (optional)")
        new_singer_folder = st.text_input("Folder path (optional, default audio/<key>)")
        if st.button("Add Singer", key="add_singer_btn"):
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
                time.sleep(0.4)
                auto_sync_songs()
                st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------- APP START ------------------
create_tables()
auto_sync_songs()

# session state defaults
if "page" not in st.session_state:
    st.session_state["page"] = "home"
if "selected_singer" not in st.session_state:
    st.session_state["selected_singer"] = None
if "playing_song" not in st.session_state:
    st.session_state["playing_song"] = None

# inject css
st.markdown(BASE_CSS, unsafe_allow_html=True)

# main content area
st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)  # small top spacing

if st.session_state["page"] == "home":
    home_view()
elif st.session_state["page"] == "songs":
    if st.session_state["selected_singer"]:
        songs_view(st.session_state["selected_singer"])
    else:
        st.session_state["page"] = "home"
        st.experimental_rerun()
elif st.session_state["page"] == "favorites":
    favorites_view()
elif st.session_state["page"] == "admin":
    admin_view()
else:
    home_view()

# bottom navigation (mobile style)
bottom_html = """
<div class="bottom-nav">
  <form action="#" method="get" style="width:100%; display:flex; justify-content:space-around;">
    <button name="nav" value="home" class="btn">🏠<div style="font-size:11px;">Home</div></button>
    <button name="nav" value="favorites" class="btn">❤️<div style="font-size:11px;">Fav</div></button>
    <button name="nav" value="admin" class="btn">⚙️<div style="font-size:11px;">Admin</div></button>
  </form>
</div>
<script>
  // map clicks to streamlit via setting localStorage and dispatching
  const btns = document.querySelectorAll('.bottom-nav button');
  btns.forEach(b=>{
    b.onclick = (e)=>{
      e.preventDefault();
      const v = b.getAttribute('value') || b.getAttribute('name') || b.value;
      // communicate via window.name hack (Streamlit can't receive this directly),
      // fallback: set location hash
      window.location.hash = 'nav-'+v;
    }
  });
  // observe hash changes - Streamlit can't directly read it, but we will also render real buttons below for server-side
</script>
"""
st.markdown(bottom_html, unsafe_allow_html=True)

# Real control buttons (invisible) so clicks work on server side for both desktop & mobile:
col1, col2, col3 = st.columns([1,1,1])
with col1:
    if st.button("🏠 Home", key="nav_home_btn"):
        st.session_state["page"] = "home"
        st.session_state["selected_singer"] = None
        st.experimental_rerun()
with col2:
    if st.button("❤️ Favorites", key="nav_fav_btn"):
        st.session_state["page"] = "favorites"
        st.session_state["selected_singer"] = None
        st.experimental_rerun()
with col3:
    if st.button("⚙️ Admin", key="nav_admin_btn"):
        st.session_state["page"] = "admin"
        st.session_state["selected_singer"] = None
        st.experimental_rerun()

# sticky bottom player
show_sticky_player_if_playing()
