from collections import Counter
from functools import partial
from typing import Callable, Collection, List, Mapping, Optional, Sequence

import httpx
import jinja2
from socketIO_client import SocketIO

from volco.renderer import extract_progress, render_playlist_page

from .constants import (
    LATEST_50_NAME,
    N_LATEST,
    PLAYLIST_HTML_DIR,
    PLAYLIST_PATTERNS,
    PLAYLIST_TEMPLATE_HTML,
    REFRESH_LOG_PATH,
    SOCKETIO_PORT,
    TEMPLATE_DIR,
    VOLUMIO_API_URL,
    VOLUMIO_URL,
)
from .controller import VolumioController
from .models import BrowseResponse, ListItem

StopCondition = Callable[[Collection[ListItem]], bool]


def stop_on_max_tracks(tracks: Collection[ListItem], max_tracks: int = 1000) -> bool:
    return len(tracks) > max_tracks


def stop_on_overlap(
    tracks: Collection[ListItem],
    existing_tracks: Collection[ListItem],
    min_overlap: int = 1,
) -> bool:
    track_uris = set(t.stripped_uri for t in tracks)
    existing_track_uris = set(t.stripped_uri for t in existing_tracks)
    overlap = set(track_uris).intersection(existing_track_uris)
    return len(overlap) >= min_overlap


def browse_tracks(
    uri: str, stop_condition: Optional[StopCondition] = None
) -> List[ListItem]:
    if stop_condition is None:
        stop_condition = partial(stop_on_max_tracks, max_tracks=5000)

    all_tracks: list[ListItem] = []

    while not stop_condition(all_tracks):
        r = httpx.get(f"http://{VOLUMIO_API_URL}/api/v1/browse?uri={uri}")
        browse_json = r.json()
        browse_response = BrowseResponse.parse_obj(browse_json)

        list_items = browse_response.navigation.lists[-1].items  # TODO: fix lists[-1]

        for item in list_items:
            if item.type not in {"song", "folder"} or item in all_tracks:
                continue
            all_tracks.append(item)

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

    return all_tracks


def filter_tracks(
    tracks: Sequence[ListItem], patterns: Collection[str]
) -> List[ListItem]:
    return [
        track
        for track in tracks
        if any(pattern in track.title.lower() for pattern in patterns)
    ]


def remove_playlist_duplicates(playlist: str, controller: VolumioController) -> None:
    playlist_tracks = browse_tracks(f"playlists/{playlist}")

    track_counter = Counter(playlist_tracks)
    for track, count in track_counter.items():
        for _ in range(count - 1):
            print(f"Removing {track.title}")
            controller.remove_from_playlist(
                playlist, service=track.service, uri=track.uri
            )


def update_new_additions_playlist(
    tracks: Collection[ListItem], vc: VolumioController
) -> None:
    new_tracks = list(tracks)[:N_LATEST]
    current_tracks = browse_tracks(f"playlists/{LATEST_50_NAME}")

    for track in new_tracks:
        vc.add_to_playlist(
            playlist=LATEST_50_NAME, service=track.service, uri=track.uri
        )
    extra = len(current_tracks) + len(new_tracks) - N_LATEST

    for idx in range(extra):
        track = current_tracks[idx]
        vc.remove_from_playlist(
            playlist=LATEST_50_NAME, service=track.service, uri=track.uri
        )


def generate_html_files(
    vc: VolumioController,
    playlists: Collection[str] = None,
    track_progress: Optional[Mapping[str, int]] = None,
) -> None:
    if playlists is None:
        playlists = vc.list_playlists()
    if track_progress is None:
        track_progress = {}

    loader = jinja2.FileSystemLoader(TEMPLATE_DIR)
    environment = jinja2.Environment(loader=loader)
    template = environment.get_template(PLAYLIST_TEMPLATE_HTML)

    for playlist in playlists:
        tracks = vc.list_tracks(playlist)

        rendered = render_playlist_page(
            title=playlist,
            tracks=tracks,
            track_progress=track_progress,
            template=template,
        )

        stripped = strip_name(playlist)
        output_path = PLAYLIST_HTML_DIR / f"{stripped}.html"
        output_path.write_text(rendered)


def strip_name(name: str) -> str:
    return name.replace(" ", "_").replace(",", "_")


def find_candidate_tracks() -> List[ListItem]:
    # TODO: this uses REST API
    existing_tracks = browse_tracks(f"playlists/{LATEST_50_NAME}")
    stop_condition = partial(
        stop_on_overlap, existing_tracks=existing_tracks, min_overlap=5
    )

    # TODO: get from config
    print("Getting nts tracks")
    candidate_tracks = browse_tracks(
        "mixcloud/user@username=NTSRadio", stop_condition=stop_condition
    )

    return candidate_tracks


def update_playlists(
    new_feed_tracks: Collection[ListItem],
    playlist_patterns: Mapping[str, Collection[str]],
    vc: VolumioController,
) -> None:
    all_new_tracks: set[ListItem] = set()

    for playlist, patterns in playlist_patterns.items():
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

            print(f"Adding track `{track.title}` to playlist `{playlist}`.")
            vc.add_to_playlist(playlist, service="mixcloud", uri=track.stripped_uri)

            all_new_tracks.add(track)

    update_new_additions_playlist(all_new_tracks, vc=vc)


def main():
    socketio = SocketIO(VOLUMIO_URL, SOCKETIO_PORT)
    vc = VolumioController(socketio)

    new_feed_tracks = find_candidate_tracks()
    update_playlists(new_feed_tracks, playlist_patterns=PLAYLIST_PATTERNS, vc=vc)

    logs = REFRESH_LOG_PATH.read_text().splitlines()
    track_progress = extract_progress(logs)

    print(track_progress)
    generate_html_files(vc=vc, track_progress=track_progress)


if __name__ == "__main__":
    main()
