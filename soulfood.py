import streamlit as st
from pathlib import Path
import os
import sqlite3
import base64
import time
from streamlit_autorefresh import st_autorefresh

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="SoulFood 🎵", layout="wide", page_icon="🎶")
# ✅ Custom Sidebar Toggle Button for Mobile
toggle_sidebar_js = """
    <script>
        function toggleSidebar() {
            var sidebar = parent.document.querySelector('section[data-testid="stSidebar"]');
            if (sidebar.style.transform === 'translateX(-100%)') {
                sidebar.style.transform = 'translateX(0)';
            } else {
                sidebar.style.transform = 'translateX(-100%)';
            }
        }
    </script>

    <style>
        .sidebar-toggle {
            position: fixed;
            top: 15px;
            left: 15px;
            background-color: #007BFF;
            color: white;
            padding: 10px 14px;
            font-size: 20px;
            border-radius: 8px;
            cursor: pointer;
            z-index: 1000;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }

        /* ✅ Sidebar visible by default on all screens */
        @media (max-width: 768px) {
            section[data-testid="stSidebar"] {
                transform: translateX(0);
                transition: transform 0.3s ease-in-out;
            }
        }
    </style>

    <div class="sidebar-toggle" onclick="toggleSidebar()">☰</div>
"""
st.markdown(toggle_sidebar_js, unsafe_allow_html=True)


# ---- Hide Streamlit Branding (Footer + Header + Menu Icon) ----
hide_streamlit_style = """
    <style>
    /* Hide Streamlit Branding Only (Safe for Mobile) */
    [data-testid="stToolbar"] {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header {visibility: hidden !important;}

    /* DO NOT HIDE MainMenu this way – it breaks mobile */
    /* Instead do this: */
    [data-testid="main-menu"] {display: none !important;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# ---------------------- DATABASE -------------------
DB_PATH = "database.db"


def get_conn():
    # Use a simple sqlite connection; for multi-threaded apps you'd adjust check_same_thread
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
        return f"data:image/jpeg;base64,{b64}"
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
    # st.toast may not exist in some versions
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
    # stop playing if the deleted song was playing
    if st.session_state.get("playing_song") == song_id:
        st.session_state["playing_song"] = None
    # Explicit rerun (works across versions)
    st.rerun()


# ---------------------- CSS ------------------------
st.markdown(
    """
<style>
body {
    background-color: #f6f9fc;
}
.center { text-align: center; }
.singer-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 35px;
    margin-top: 30px;
    width: 100%;
    max-width: 950px;
    margin-left: auto;
    margin-right: auto;
}
.singer-card {
    background-color: white;
    border-radius: 18px;
    padding: 15px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
}
.singer-card:hover { transform: translateY(-8px); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }
.singer-img {
    width: 160px;
    height: 160px;
    border-radius: 50%;
    object-fit: cover;
    margin-bottom: 12px;
    border: 3px solid #007BFF;
}
.song-grid {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 25px;
}
.song-card {
    background: white;
    border-radius: 15px;
    width: 280px;
    padding: 15px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    transition: 0.3s;
}
.song-card:hover { transform: scale(1.03); }
.song-card audio { width: 100%; }
h1.title {
    color: #007BFF;
    text-align: center;
    margin-top: 10px;
    font-weight: bold;
}
h3.subtitle {
    color: black;
    text-align: center;
    margin-bottom: 25px;
}
.verse-box {
    background-color: #e8f0fe;
    border-left: 5px solid #007BFF;
    border-radius: 10px;
    padding: 10px 15px;
    text-align: center;
    font-style: italic;
    color: #000;
    font-size: 17px;
    margin-top: 10px;
    width: 70%;
    margin-left: auto;
    margin-right: auto;
    animation: fadeIn 1s ease-in-out;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------- HEADER ---------------------


def show_header():
    # Auto refresh every 30s
    st_autorefresh(interval=30000, key="verse_refresh")

    st.markdown("<h1 class='title'>🎵 SoulFood – پرستش 🎵</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='center' style='font-size:16px;'>Gospel Music Player</p>",
        unsafe_allow_html=True,
    )
    verse_index = int(time.time() / 30) % len(BIBLE_VERSES)
    verse = BIBLE_VERSES[verse_index]
    st.markdown(f"<div class='verse-box'>{verse}</div>", unsafe_allow_html=True)
    st.markdown("---")


# ---------------------- VIEWS ----------------------
def show_singers():
    show_header()
    # ✅ Add this here:
    st.info("""
    📱 **Mobile Users:**  
    - Top left corner par **≡ icon** ko tap karein.  
    - Wahan se **Upload Song / Admin Panel** ka option milega.  
    """)

    st.markdown("<h3 class='subtitle'>Select a Singer</h3>", unsafe_allow_html=True)
    st.markdown('<div class="singer-row">', unsafe_allow_html=True)

    for key, data in SINGERS.items():
        img_src = image_to_base64(data["image"]) if os.path.exists(data["image"]) else ""
        # Render a card for singer
        st.markdown(
            f"""
        <div class="singer-card">
            <img src="{img_src}" class="singer-img" alt="{data['name']}">
            <h4>{data['name']}</h4>
        </div>
        """,
            unsafe_allow_html=True,
        )
        # Button to select singer
        if st.button(f"🎤 Listen to {data['name']}", key=f"btn_{key}"):
            st.session_state["selected_singer"] = key
            st.session_state["show_favorites"] = False
            # stop any playing song when switching views
            st.session_state["playing_song"] = None
            # Streamlit auto re-runs on interaction; still we explicitly rerun to ensure immediate change
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def show_songs(singer_key):
    show_header()
    songs = get_songs_by_singer(singer_key)
    fav_ids = get_favorites()

    st.markdown(f"<h3 class='subtitle'>{SINGERS[singer_key]['name']} Songs</h3>", unsafe_allow_html=True)

    # ✅ Back Button at Top
    if st.button("⬅️ Back to Singers", key="back_top"):
        st.session_state["selected_singer"] = None
        st.session_state["playing_song"] = None
        st.session_state["show_favorites"] = False
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    if not songs:
        st.info("No songs found for this singer.")
        return

    # ✅ Song Cards
    st.markdown('<div class="song-grid">', unsafe_allow_html=True)

    for song_id, title, file_path in songs:
        fav_heart = "❤️" if song_id in fav_ids else "🤍"
        with st.container():
            st.markdown(
                f"<div class='song-card'>"
                f"<h4>🎵 {title}</h4>",
                unsafe_allow_html=True,
            )

            # Only show audio player for currently playing song
            if st.session_state.get("playing_song") == song_id:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "rb") as f:
                            st.audio(f.read(), format="audio/mp3")
                    except Exception:
                        st.warning("⚠️ Failed to load audio file.")
                else:
                    st.warning("⚠️ Audio file missing!")

            # Buttons
            c1, c2, c3 = st.columns(3)
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
    # Protect against empty list — handled above
    placeholders = ",".join(["?"] * len(fav_ids))
    cur.execute(f"SELECT id, title, file_path FROM songs WHERE id IN ({placeholders})", fav_ids)
    favs = cur.fetchall()
    conn.close()

    st.markdown("<h3 class='subtitle'>❤️ Your Favorite Songs</h3>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Singers"):
        st.session_state["show_favorites"] = False
        st.session_state["selected_singer"] = None
        st.session_state["playing_song"] = None
        st.rerun()

    for song_id, title, file_path in favs:
        with st.container():
            st.markdown(
                f"<div style='text-align:center; background:#fff; padding:15px; "
                f"border-radius:15px; box-shadow:0 4px 12px rgba(0,0,0,0.1); margin-bottom:20px;'>"
                f"<h4>🎵 {title}</h4>",
                unsafe_allow_html=True,
            )

            # Only show audio player for the currently playing song.
            if st.session_state.get("playing_song") == song_id:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "rb") as f:
                            audio_bytes = f.read()
                        st.audio(audio_bytes, format="audio/mp3")
                    except Exception:
                        st.warning("⚠️ Failed to load audio file.")
                else:
                    st.warning("⚠️ Audio file missing!")

            c1, c2 = st.columns(2)
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

# initialize session state keys if missing
if "selected_singer" not in st.session_state:
    st.session_state["selected_singer"] = None
if "show_favorites" not in st.session_state:
    st.session_state["show_favorites"] = False
if "playing_song" not in st.session_state:
    st.session_state["playing_song"] = None

# ---------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown("<h4 style='text-align:center; color:#007BFF;'>🎧 Admin Panel – Add New Song</h4>", unsafe_allow_html=True)
    with st.form("upload_form", clear_on_submit=True):
        singer_choice = st.selectbox("Select Singer", list(SINGERS.keys()), format_func=lambda x: SINGERS[x]["name"])
        song_title = st.text_input("Song Title")
        uploaded_file = st.file_uploader("Upload MP3 File", type=["mp3"])
        submitted = st.form_submit_button("Upload Song")

        if submitted and uploaded_file and song_title:
            dest_folder = Path(SINGERS[singer_choice]["folder"])
            dest_folder.mkdir(parents=True, exist_ok=True)
            # sanitize filename: replace spaces
            safe_name = uploaded_file.name.replace(" ", "_")
            dest_path = dest_folder / safe_name
            # If same filename exists, append timestamp
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
            success_placeholder = st.empty()
            success_placeholder.success(f"✅ Song '{song_title}' uploaded successfully!")
            time.sleep(1.2)
            success_placeholder.empty()
            # after upload, sync and refresh
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
