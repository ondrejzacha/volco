from pathlib import Path

VOLUMIO_URL = "192.168.2.22"
SOCKETIO_PORT = 3000
TEMPLATE_DIR = Path("/templates")
PLAYLIST_HTML_DIR = Path("/static/playlists/")  # TODO: auto mkdir
PLAYLIST_TEMPLATE_HTML = "list.html"
LATEST_50_NAME = "- latest 50"
N_LATEST = 50


ALL_PLAYLISTS = [
    "- aaa",
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
    "- fergus clark, optimo, lukid": ["fergus clark", "optimo", "lukid",],
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
    "- smart dancey": ["batu", "dj nobu", "four tet", "ben ufo", "upsammy",],
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
    "- ambi": ["malibu", "carla dal forno", "sofie birch", "yu su", "astrid sonne",],
    "- nordi": ["posh isolation", "oqbqbo", "scandinavian star", "croatian amor",],
}

HEADERS = [
    # Firefox 77 Mac
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    },
    # Firefox 77 Windows
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    },
    # Chrome 83 Mac
    {
        "Connection": "keep-alive",
        "DNT": "1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://www.google.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    },
    # Chrome 83 Windows
    {
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Referer": "https://www.google.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
    },
]
