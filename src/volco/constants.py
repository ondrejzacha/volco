from pathlib import Path

# VOLUMIO_URL = "192.168.2.22"
VOLUMIO_URL = "localhost"
SOCKETIO_PORT = 3000
VOLUMIO_API_URL = f"{VOLUMIO_URL}:3000"

TEMPLATE_DIR = Path("templates")
PLAYLIST_HTML_DIR = Path("static/playlists/")  # TODO: auto mkdir
PLAYLIST_PATTERN_PATH = Path("static/playlist_patterns.json")
PLAYLIST_TEMPLATE_HTML = "list.html"
LATEST_50_NAME = "- latest 50"
N_LATEST = 50

STATE_LOG_PATH = Path("logs/state.log")


ALL_PLAYLISTS = [
    "- ad93, tasker",
    "- ambi",
    "- dark dancey",
    "- demanding",
    "- fergus clark, optimo, lukid",
    "- fun dancey",
    "- john gomez, mr pedro, dj python, felix hall",
    "- latest 50",
    "- lupini",
    "- maria, spirit blue",
    "- nordi",
    "- smart dancey",
    "jazzy?",
    "later",
    "main",
    "mixes for a curious mind",
    "nts",
    "undefined",
    "upbeat",
]
