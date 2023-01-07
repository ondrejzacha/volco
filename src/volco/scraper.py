from collections import Counter
from datetime import datetime
from functools import partial
from typing import Callable, Collection, List, Optional, Sequence
import logging

import httpx
import jinja2
from socketIO_client import SocketIO

from .constants import (
    LATEST_50_NAME,
    N_LATEST,
    PLAYLIST_HTML_DIR,
    PLAYLIST_PATTERNS,
    PLAYLIST_TEMPLATE_HTML,
    SOCKETIO_PORT,
    TEMPLATE_DIR,
    VOLUMIO_URL,
    VOLUMIO_API_URL,
)
from .controller import VolumioController
from .models import BrowseResponse, ListItem

logger = logging.getLogger(__name__)

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
            logger.debug("No more pages")
            break

        logger.debug(".", end="")
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
            logger.info(f"Removing {track.title} from playlist {playlist}.")
            controller.remove_from_playlist(
                playlist, service=track.service, uri=track.uri
            )


def update_new_additions_playlist(
    tracks: Collection[ListItem], controller: VolumioController
) -> None:
    new_tracks = list(tracks)[:N_LATEST]
    current_tracks = browse_tracks(f"playlists/{LATEST_50_NAME}")

    # Add new tracks
    for track in new_tracks:
        logger.info(f"Adding track {track.title} to playlist {LATEST_50_NAME}")
        controller.add_to_playlist(
            playlist=LATEST_50_NAME, service=track.service, uri=track.uri
        )

    # Remove oldest tracks to reach N_LATEST
    extra = len(current_tracks) + len(new_tracks) - N_LATEST
    for idx in range(extra):
        track = current_tracks[idx]
        controller.remove_from_playlist(
            playlist=LATEST_50_NAME, service=track.service, uri=track.uri
        )


def generate_html_files(
    vc: VolumioController, playlists: Collection[str] = None
) -> None:
    if playlists is None:
        # TODO: better response
        playlists = vc.list_playlists().__root__

    loader = jinja2.FileSystemLoader(TEMPLATE_DIR)
    environment = jinja2.Environment(loader=loader)
    template = environment.get_template(PLAYLIST_TEMPLATE_HTML)

    for playlist in playlists:
        tracks = vc.list_tracks(playlist)
        # TODO: smarter tracks[::-1]
        rendered = template.render(
            {
                "playlist_name": playlist,
                "tracks": tracks.navigation.lists[-1].items[::-1],
                "ts": datetime.now(),
            }
        )
        stripped = strip_name(playlist)
        output_path = PLAYLIST_HTML_DIR / f"{stripped}.html"
        output_path.write_text(rendered)


def strip_name(name: str) -> str:
    return name.replace(" ", "_").replace(",", "_")


def main():
    logging.basicConfig(level="INFO")

    socketio = SocketIO(VOLUMIO_URL, SOCKETIO_PORT)
    vc = VolumioController(socketio)

    existing_tracks = browse_tracks(f"playlists/{LATEST_50_NAME}")
    stop_condition = partial(
        stop_on_overlap, existing_tracks=existing_tracks, min_overlap=5
    )

    logger.info("Getting nts tracks")
    new_feed_tracks = browse_tracks(
        "mixcloud/user@username=NTSRadio", stop_condition=stop_condition
    )

    all_new_tracks: set[ListItem] = set()

    for playlist, patterns in PLAYLIST_PATTERNS.items():
        logger.debug(f"Handling playlist `{playlist}`")
        current_tracks = browse_tracks(f"playlists/{playlist}")
        current_uris = set(track.stripped_uri for track in current_tracks)
        matching_tracks = filter_tracks(new_feed_tracks, patterns)

        for track in matching_tracks:
            if track.stripped_uri in current_uris:
                logger.debug(
                    f"Skipping track `{track.title}` as "
                    f"it already is in playlist `{playlist}`."
                )
                continue

            logger.info(f"Adding track `{track.title}` to playlist `{playlist}`.")
            vc.add_to_playlist(playlist, service="mixcloud", uri=track.stripped_uri)

            all_new_tracks.add(track)

    update_new_additions_playlist(all_new_tracks, controller=vc)

    generate_html_files(vc=vc)


if __name__ == "__main__":
    main()
