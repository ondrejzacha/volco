from collections import Counter
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


def remove_playlist_duplicates(
    playlist: str, volumio_controller: VolumioController
) -> None:
    playlist_tracks = browse_tracks(f"playlists/{playlist}")

    track_counter = Counter(playlist_tracks)
    for track, count in track_counter.items():
        for _ in range(count - 1):
            print(f"Removing {track.title}")
            volumio_controller.remove_from_playlist(
                playlist, TrackSpec(service=track.service, uri=track.uri)
            )


LATEST_50_NAME = "- latest 50"
N_LATEST = 50


def update_new_additions_playlist(
    tracks: Collection[ListItem], volumio_controller: VolumioController
) -> None:
    new_tracks = list(tracks)[:N_LATEST]
    current_tracks = browse_tracks(f"playlists/{LATEST_50_NAME}")

    for track in new_tracks:
        volumio_controller.add_to_playlist(
            LATEST_50_NAME, TrackSpec(service=track.service, uri=track.uri)
        )
    extra = len(current_tracks) + len(new_tracks) - N_LATEST

    for idx in range(extra):
        track = current_tracks[idx]
        volumio_controller.remove_from_playlist(
            LATEST_50_NAME, TrackSpec(service=track.service, uri=track.uri)
        )


def main():
    socketio = SocketIO("192.168.2.22", 3000)
    vc = VolumioController(socketio)
    print("Getting nts tracks")
    new_feed_tracks = browse_tracks("mixcloud/user@username=NTSRadio", max_tracks=1000)

    all_new_tracks = set()

    for playlist, patterns in PLAYLIST_PATTERNS.items():
        print(f"Handling playlist `{playlist}`")
        current_tracks = browse_tracks(f"playlists/{playlist}")
        current_uris = set(track.stripped_uri for track in current_tracks)
        matching_tracks = filter_tracks(new_feed_tracks, patterns)

        for track in matching_tracks:
            if track.stripped_uri in current_uris:
                print(
                    f"Skipping track `{track.title}` as "
                    f"it already is in playlist `{playlist}`."
                )
                continue

            track_spec = TrackSpec(service="mixcloud", uri=track.stripped_uri)
            print(f"Adding track `{track.title}` to playlist `{playlist}`.")
            vc.add_to_playlist(playlist, track_spec=track_spec)

            all_new_tracks.add(track_spec)

    update_new_additions_playlist(all_new_tracks, volumio_controller=vc)

    # generate_html_files(all_playlists)
