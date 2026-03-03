# TODO: move this to config

import os
from pathlib import Path

TEMPLATE_DIR = Path("templates")
PLAYLIST_HTML_DIR = Path("static/playlists/")  # TODO: auto mkdir
PLAYLIST_PATTERN_PATH = Path("static/playlist_patterns.json")
INDEX_PATH = Path("static/index.html")
PLAYLIST_TEMPLATE_HTML = "list.html"
INDEX_TEMPLATE_HTML = "index.html"

if not PLAYLIST_PATTERN_PATH.exists():
    PLAYLIST_PATTERN_PATH.write_text("{}")

LATEST_50_NAME = "- latest 50"
N_LATEST = 50

STATE_LOG_PATH = Path("logs/state.log")
TRACK_PROGRESS_PATH = Path("logs/track_progress.json")
CANDIDATE_TRACKS_PATH = Path("logs/candidate_tracks.json")

TRACK_SOURCES = [
    "soundcloud/tracks@userId=995174173",  # NTS Monday
    "soundcloud/tracks@userId=995174689",  # NTS Tuesday
    "soundcloud/tracks@userId=995898355",  # NTS Wednesday
    # "soundcloud/tracks@userId=995897410",  # NTS Thursday
    "soundcloud/tracks@userId=995888653",  # NTS Friday
    # "soundcloud/tracks@userId=995579326",  # NTS Saturday
    "soundcloud/tracks@userId=995580424",  # NTS Sunday
    "soundcloud/tracks@userId=995579326",  # NTS 2024-2025
    "soundcloud/tracks@userId=995897410",  # NTS Latest
]

SOCKETIO_PORT = 3000
VOLUMIO_URL = os.environ.get("VOLUMIO_URL", "localhost")

VOLUMIO_API_URL = f"{VOLUMIO_URL}:3000"
