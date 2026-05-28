import streamlit as st
import sqlite3
import pandas as pd
import re

st.set_page_config(
    page_title="MP3 Collection",
    page_icon="🐲",
    layout="wide"
)

# =========================================================
# STYLE
# =========================================================

st.markdown("""
<style>

.block-container {
    max-width: 1750px;
    padding-top: 1rem;
}

[data-testid="stSidebar"] {
    background-color: #101010;
}

div.stButton > button {
    width: 100%;
    text-align: left;
    background-color: #1b1b1b;
    color: white;
    border: 1px solid #333;
    border-radius: 8px;
}

div.stButton > button:hover {
    border: 1px solid #39ff14;
    color: #39ff14;
}

.section-header {
    margin-top: 30px;
    margin-bottom: 10px;
    padding-bottom: 5px;
    border-bottom: 2px solid #444;
    font-size: 28px;
    font-weight: bold;
}

.sub-header {
    margin-top: 20px;
    margin-bottom: 8px;
    font-size: 22px;
    font-weight: bold;
    color: #39ff14;
}

.stTextInput input {
    background-color: #222 !important;
    color: white !important;
    border: 1px solid #555 !important;
    border-radius: 8px !important;
}

.track-number {
    text-align: center;
    font-weight: bold;
    color: #39ff14;
    padding-top: 5px;
    font-size: 16px;
}

.album-total {
    margin-top: 10px;
    margin-bottom: 25px;
    font-size: 14px;
    color: #bbbbbb;
    border-top: 1px solid #333;
    padding-top: 5px;
}

.logo-dragon {
    text-align: center;
    padding-top: 10px;
    padding-bottom: 18px;
}

.logo-dragon-icon {
    font-size: 120px;
    line-height: 120px;
}

.logo-dragon-text {
    color: #39ff14;
    font-size: 46px;
    font-weight: bold;
    font-family: Impact, sans-serif;
    letter-spacing: 3px;
    text-shadow: 3px 3px #000000;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# DB
# =========================================================

@st.cache_resource
def get_connection():

    return sqlite3.connect(
        "music.db",
        check_same_thread=False
    )

conn = get_connection()

# =========================================================
# SESSION
# =========================================================

defaults = {
    "view": "artists",
    "artist": None,
    "album": None,
    "cd": None,
    "history": [],
    "artist_filter": "",
    "album_filter": ""
}

for k, v in defaults.items():

    if k not in st.session_state:
        st.session_state[k] = v

# =========================================================
# HELPERS
# =========================================================

def push_history():

    current = {
        "view": st.session_state.view,
        "artist": st.session_state.artist,
        "album": st.session_state.album,
        "cd": st.session_state.cd
    }

    if (
        len(st.session_state.history) == 0
        or st.session_state.history[-1] != current
    ):
        st.session_state.history.append(current)

def go_back():

    if len(st.session_state.history) > 1:

        st.session_state.history.pop()

        previous = st.session_state.history[-1]

        st.session_state.view = previous["view"]
        st.session_state.artist = previous["artist"]
        st.session_state.album = previous["album"]
        st.session_state.cd = previous["cd"]

def open_artist(name):

    st.session_state.view = "artist"
    st.session_state.artist = name

    push_history()

def open_album(artist, album):

    st.session_state.view = "album"
    st.session_state.artist = artist
    st.session_state.album = album

    push_history()

def open_cd(cd):

    st.session_state.view = "cd"
    st.session_state.cd = cd

    push_history()

# =========================================================
# TRACK NUMBER
# =========================================================

def extract_track_number(title):

    if not title:
        return 9999

    title = str(title).strip()

    patterns = [
        r"^\s*(\d{1,3})\s*-\s*",
        r"^\s*(\d{1,3})\.",
        r"^\s*(\d{1,3})\s+",
        r"^track\s*(\d{1,3})",
        r"^(\d{1,3})$"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            title,
            re.IGNORECASE
        )

        if match:

            try:
                return int(match.group(1))
            except:
                pass

    return 9999

def track_display(title):

    n = extract_track_number(title)

    if n == 9999:
        return ""

    return str(n)

# =========================================================
# TIME
# =========================================================

def time_to_seconds(t):

    try:

        m, s = t.split(":")
        return int(m) * 60 + int(s)

    except:
        return 0

def seconds_to_time(sec):

    m = sec // 60
    s = sec % 60

    return f"{m:02}:{s:02}"

# =========================================================
# RESULTS
# =========================================================

def render_results(df):

    if len(df) == 0:
        st.warning("No results")
        return

    df = df.copy()

    df["track_order"] = df["title"].apply(
        extract_track_number
    )

    df = df.sort_values(
        by=[
            "artist",
            "album",
            "track_order"
        ],
        kind="stable"
    )

    header = st.columns([3,3,1,5,1,1])

    header[0].markdown("**Artist**")
    header[1].markdown("**Album**")
    header[2].markdown("**#**")
    header[3].markdown("**Title**")
    header[4].markdown("**Time**")
    header[5].markdown("**CD**")

    current_album = None
    album_seconds = 0

    for idx, row in df.iterrows():

        album_key = (
            f"{row['artist']}___{row['album']}"
        )

        if (
            current_album is not None
            and current_album != album_key
        ):

            st.markdown(
                f"""
                <div class="album-total">
                ⏱ Total album time:
                {seconds_to_time(album_seconds)}
                </div>
                """,
                unsafe_allow_html=True
            )

            album_seconds = 0

        if album_key != current_album:

            current_album = album_key

            st.markdown(
                f"""
                <div class="sub-header">
                💿 {row['artist']} — {row['album']}
                </div>
                """,
                unsafe_allow_html=True
            )

        album_seconds += time_to_seconds(
            row["duration"]
        )

        cols = st.columns([3,3,1,5,1,1])

        with cols[0]:

            if st.button(
                row["artist"],
                key=f"artist_{idx}"
            ):
                open_artist(row["artist"])
                st.rerun()

        with cols[1]:

            if st.button(
                row["album"],
                key=f"album_{idx}"
            ):
                open_album(
                    row["artist"],
                    row["album"]
                )
                st.rerun()

        cols[2].markdown(
            f"""
            <div class="track-number">
            {track_display(row["title"])}
            </div>
            """,
            unsafe_allow_html=True
        )

        cols[3].write(row["title"])
        cols[4].write(row["duration"])

        with cols[5]:

            if st.button(
                row["cd_location"],
                key=f"cd_{idx}"
            ):
                open_cd(
                    row["cd_location"]
                )
                st.rerun()

    st.markdown(
        f"""
        <div class="album-total">
        ⏱ Total album time:
        {seconds_to_time(album_seconds)}
        </div>
        """,
        unsafe_allow_html=True
    )

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div class="logo-dragon">
            <div class="logo-dragon-icon">🐲</div>
            <div class="logo-dragon-text">
                MP3 Collection
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button(
        "Home",
        key="home_logo"
    ):
        st.session_state.view = "artists"
        st.rerun()

search = st.sidebar.text_input("Search")

if st.sidebar.button("⬅ Back"):
    go_back()
    st.rerun()

if st.sidebar.button("🎤 Artists"):
    st.session_state.view = "artists"
    st.rerun()

if st.sidebar.button("💿 Albums"):
    st.session_state.view = "albums"
    st.rerun()

if st.sidebar.button("📀 CDs"):
    st.session_state.view = "cds"
    st.rerun()

if st.sidebar.button("📊 Stats"):
    st.session_state.view = "stats"
    st.rerun()

# =========================================================
# SEARCH
# =========================================================

if search:

    st.title(f"🔎 Search: {search}")

    tokens = search.strip().split()

    fts_query = " ".join(
        [f"{t}*" for t in tokens]
    )

    query = """
    SELECT
        songs.artist,
        songs.album,
        songs.title,
        songs.duration,
        songs.cd_location
    FROM song_search
    JOIN songs
    ON song_search.rowid = songs.id
    WHERE song_search MATCH ?
    LIMIT 1000
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(fts_query,)
    )

    st.write(f"{len(df)} results")

    render_results(df)

elif st.session_state.view == "artists":

    st.title("🎤 Artists")

    st.text_input(
        "Filter artists",
        key="artist_filter"
    )

    query = """
    SELECT DISTINCT artist
    FROM songs
    ORDER BY artist
    """

    artists = pd.read_sql_query(
        query,
        conn
    )

    if st.session_state.artist_filter:

        artists = artists[
            artists["artist"].str.contains(
                st.session_state.artist_filter,
                case=False,
                na=False
            )
        ]

    current_letter = None

    for idx, row in artists.iterrows():

        artist = row["artist"]

        if not artist:
            continue

        first = artist[0].upper()

        if first != current_letter:

            current_letter = first

            st.markdown(
                f"""
                <div class="section-header">
                {first}
                </div>
                """,
                unsafe_allow_html=True
            )

        if st.button(
            artist,
            key=f"artistlist_{idx}"
        ):
            open_artist(artist)
            st.rerun()

elif st.session_state.view == "artist":

    artist = st.session_state.artist

    st.title(f"🎤 {artist}")

    query = """
    SELECT
        artist,
        album,
        title,
        duration,
        cd_location
    FROM songs
    WHERE artist = ?
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(artist,)
    )

    render_results(df)

elif st.session_state.view == "albums":

    st.title("💿 Albums")

    st.text_input(
        "Filter albums",
        key="album_filter"
    )

    query = """
    SELECT
        artist,
        album,
        COUNT(*) as tracks
    FROM songs
    GROUP BY artist, album
    ORDER BY artist, album
    """

    albums = pd.read_sql_query(
        query,
        conn
    )

    if st.session_state.album_filter:

        albums = albums[
            albums["album"].str.contains(
                st.session_state.album_filter,
                case=False,
                na=False
            )
            |
            albums["artist"].str.contains(
                st.session_state.album_filter,
                case=False,
                na=False
            )
        ]

    current_artist = None

    for idx, row in albums.iterrows():

        artist = row["artist"]

        if artist != current_artist:

            current_artist = artist

            st.markdown(
                f"""
                <div class="section-header">
                🎤 {artist}
                </div>
                """,
                unsafe_allow_html=True
            )

        label = (
            f"{row['album']} "
            f"({row['tracks']} tracks)"
        )

        if st.button(
            label,
            key=f"albums_{idx}"
        ):
            open_album(
                row["artist"],
                row["album"]
            )
            st.rerun()

elif st.session_state.view == "album":

    artist = st.session_state.artist
    album = st.session_state.album

    st.title(f"💿 {album}")
    st.caption(artist)

    query = """
    SELECT
        artist,
        album,
        title,
        duration,
        cd_location
    FROM songs
    WHERE artist = ?
    AND album = ?
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(artist, album)
    )

    render_results(df)

elif st.session_state.view == "cds":

    st.title("📀 CDs")

    query = """
    SELECT
        cd_location,
        COUNT(*) as tracks
    FROM songs
    GROUP BY cd_location
    ORDER BY CAST(REPLACE(cd_location, 'mp3_', '') AS INTEGER)
    """

    cds = pd.read_sql_query(
        query,
        conn
    )

    for idx, row in cds.iterrows():

        label = (
            f"{row['cd_location']} "
            f"({row['tracks']} tracks)"
        )

        if st.button(
            label,
            key=f"cds_{idx}"
        ):
            open_cd(
                row["cd_location"]
            )
            st.rerun()

elif st.session_state.view == "cd":

    cd = st.session_state.cd

    st.title(f"📀 {cd}")

    query = """
    SELECT
        artist,
        album,
        title,
        duration,
        cd_location
    FROM songs
    WHERE cd_location = ?
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(cd,)
    )

    render_results(df)

elif st.session_state.view == "stats":

    st.title("📊 Stats")

    query = """
    SELECT
        COUNT(*) as songs,
        COUNT(DISTINCT artist) as artists,
        COUNT(DISTINCT album) as albums,
        COUNT(DISTINCT cd_location) as cds
    FROM songs
    """

    stats = pd.read_sql_query(
        query,
        conn
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Songs",
        int(stats["songs"][0])
    )

    c2.metric(
        "Artists",
        int(stats["artists"][0])
    )

    c3.metric(
        "Albums",
        int(stats["albums"][0])
    )

    c4.metric(
        "CDs",
        int(stats["cds"][0])
    )