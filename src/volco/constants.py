from pathlib import Path

# VOLUMIO_URL = "192.168.2.22"
VOLUMIO_URL = "localhost"
SOCKETIO_PORT = 3000
VOLUMIO_API_URL = f"{VOLUMIO_URL}:3000"

TEMPLATE_DIR = Path("templates")
PLAYLIST_HTML_DIR = Path("static/playlists/")  # TODO: auto mkdir
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

PLAYLIST_PATTERNS = {
    "- maria, spirit blue": ["maria somerville", "spirit blue"],
    "- john gomez, mr pedro, dj python, felix hall": [
        "john gomez",
        "john gómez",
        "felix hall",
        "dj python",
        "mr pedro",
    ],
    "- fergus clark, optimo, lukid": [
        "fergus clark",
        "optimo",
        "lukid",
    ],
    "- willikens/ivkovic": ["ivkovic", "willikens"],
    "- ad93, tasker": ["ad 93", "ad93", "tasker"],
    "- lupini": ["lupini"],
    "- demanding": [
        "adam oko",
        "felisha ledesma",
        "astrid sonne",
        "sapphire slows",
        "nabihah iqbal",
    ],
    "- smart dancey": [
        "batu",
        "dj nobu",
        "four tet",
        "ben ufo",
        "upsammy",
    ],
    "- fun dancey": [
        "call super",
        "young marco",
        "carista",
        "courtesy",
        "daphni",
        "yu su",
    ],
    "- dark dancey": [
        "mark knekelhuis",
        "elena colombi",
        "silvia kastel",
        "margarita",
        "john talabot",
        "lauren duffus",
        "orpheu the wizard",
        "martha",
    ],
    "- ambi": [
        "malibu",
        "carla dal forno",
        "sofie birch",
        "yu su",
        "astrid sonne",
    ],
    "- nordi": [
        "posh isolation",
        "oqbqbo",
        "scandinavian star",
        "croatian amor",
    ],
}
