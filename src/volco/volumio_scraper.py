from typing import Collection, Sequence

import requests
from socketIO_client import SocketIO

from .constants import PLAYLIST_PATTERNS
from .volumio_controller import TrackSpec, VolumioController
from .volumio_models import BrowseResponse, ListItem

VOLUMIO_URL = "http://192.168.2.22"  # TODO: get from env


# def browse_tracks(uri: str, stop_condition: Callable[[Collection[ListItem]], bool]) -> list[ListItem]:
def browse_tracks(uri: str, max_tracks: int = 1000) -> list[ListItem]:
    all_tracks = set()

    while len(all_tracks) < max_tracks:
        r = requests.get(f"{VOLUMIO_URL}/api/v1/browse?uri={uri}")
        browse_json = r.json()
        browse_response = BrowseResponse.parse_obj(browse_json)

        list_items = browse_response.navigation.lists[-1].items  # TODO: fix lists[-1]

        track_items = set(
            item for item in list_items if item.type in {"song", "folder"}
        )
        all_tracks |= track_items

        next_page = next(
            (
                item
                for item in list_items
                if item.type in {"mixcloudNextPageItem", "soundcloudNextPageItem"}
            ),
            None,
        )
        if next_page is None:
            print("No more pages")
            break

        print(".", end="")
        uri = next_page.uri

    return list(all_tracks)


def filter_tracks(
    tracks: Sequence[ListItem], patterns: Collection[str]
) -> list[ListItem]:
    return [
        track
        for track in tracks
        if any(pattern in track.title.lower() for pattern in patterns)
    ]


def main():
    socketio = SocketIO("192.168.2.22", 3000)
    vc = VolumioController(socketio)

    new_feed_tracks = browse_tracks("mixcloud/user@username=NTSRadio", max_tracks=1000)

    all_new_tracks = set()
    # playlist_uris = {}
    for playlist, patterns in PLAYLIST_PATTERNS.items():
        new_tracks = filter_tracks(new_feed_tracks, patterns)
        # playlist_uris[playlist] = new_tracks
        for track in new_tracks:
            track_spec = TrackSpec(service="mixcloud", uri=track.stripped_uri)
            print(f"Adding track `{track.title}` to playlist `{playlist}`.")
            vc.add_to_playlist(playlist, track_spec=track_spec)

            all_new_tracks.add(track_spec)

    # update_new_additions_playlist(all_new_tracks)

    # generate_html_files(all_playlists)
