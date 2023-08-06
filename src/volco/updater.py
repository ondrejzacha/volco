import json
import logging
from collections import Counter
from functools import partial
from typing import Collection, Dict, List, Mapping, Optional, Set

import jinja2
from socketIO_client import SocketIO

from volco.controller import VolumioController
from volco.models import ListItem
from volco.renderer import extract_progress, render_index_file, render_playlist_page
from volco.scraper import browse_tracks, stop_on_overlap

from .constants import (
    INDEX_PATH,
    INDEX_TEMPLATE_HTML,
    LATEST_50_NAME,
    N_LATEST,
    PLAYLIST_HTML_DIR,
    PLAYLIST_PATTERN_PATH,
    PLAYLIST_TEMPLATE_HTML,
    SOCKETIO_PORT,
    STATE_LOG_PATH,
    TEMPLATE_DIR,
    TRACK_SOURCES,
    VOLUMIO_URL,
)

logger = logging.getLogger(__name__)


def remove_playlist_duplicates(playlist: str, controller: VolumioController) -> None:
    playlist_tracks = browse_tracks(f"playlists/{playlist}")

    track_counter = Counter(playlist_tracks)
    for track, count in track_counter.items():
        for _ in range(count - 1):
            logger.info(f"Removing {track.title} from playlist {playlist}.")
            controller.remove_from_playlist(
                playlist, service=track.service, uri=track.uri
            )


def filter_tracks(
    tracks: Collection[ListItem], patterns: Collection[str]
) -> List[ListItem]:
    return [
        track
        for track in tracks
        if any(pattern in track.title.lower() for pattern in patterns)
    ]


def update_new_additions_playlist(
    tracks: Collection[ListItem], vc: VolumioController
) -> None:
    new_tracks = list(tracks)[:N_LATEST]
    current_tracks = browse_tracks(f"playlists/{LATEST_50_NAME}")

    # Add new tracks
    for track in new_tracks:
        logger.info(f"Adding track {track.title} to playlist {LATEST_50_NAME}")
        vc.add_to_playlist(
            playlist=LATEST_50_NAME, service=track.service, uri=track.uri
        )

    # Remove oldest tracks to reach N_LATEST
    extra = len(current_tracks) + len(new_tracks) - N_LATEST
    for idx in range(extra):
        track = current_tracks[idx]
        vc.remove_from_playlist(
            playlist=LATEST_50_NAME, service=track.service, uri=track.uri
        )


def generate_html_files(
    vc: VolumioController,
    track_progress: Optional[Mapping[str, int]] = None,
) -> None:
    logger.info("Generating HTML pages for playlists.")

    loader = jinja2.FileSystemLoader(TEMPLATE_DIR)
    environment = jinja2.Environment(loader=loader)
    template = environment.get_template(PLAYLIST_TEMPLATE_HTML)

    playlists = vc.list_playlists()

    playlist_files: Dict[str, str] = {}
    for playlist in playlists:
        tracks = vc.list_tracks(playlist)

        rendered = render_playlist_page(
            title=playlist,
            tracks=tracks,
            track_progress=track_progress or {},
            template=template,
        )

        filename = generate_filename(playlist)

        playlist_files[playlist] = filename
        output_path = PLAYLIST_HTML_DIR / filename
        output_path.write_text(rendered)

    index_template = environment.get_template(INDEX_TEMPLATE_HTML)
    rendered_index = render_index_file(playlist_files, index_template)
    INDEX_PATH.write_text(rendered_index)


def generate_filename(name: str) -> str:
    name = name.replace(" ", "_")
    name = name.replace(",", "_")
    return f"{name}.html"


def find_candidate_tracks() -> List[ListItem]:
    # TODO: this uses REST API
    existing_tracks = browse_tracks(f"playlists/{LATEST_50_NAME}")
    stop_condition = partial(
        stop_on_overlap, existing_tracks=existing_tracks, min_overlap=5
    )

    all_tracks: List[ListItem] = []
    for track_source in TRACK_SOURCES:
        source_tracks = browse_tracks(track_source, stop_condition=stop_condition)
        logger.info(f"Got {len(source_tracks)} tracks from {track_source}")
        all_tracks += source_tracks

    return all_tracks


def update_playlists(
    new_feed_tracks: Collection[ListItem],
    playlist_patterns: Mapping[str, Collection[str]],
    vc: VolumioController,
) -> None:
    all_new_tracks: Set[ListItem] = set()

    for playlist, patterns in playlist_patterns.items():
        logger.info(f"Handling playlist `{playlist}`")
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
            vc.add_to_playlist(playlist, service=track.service, uri=track.stripped_uri)

            all_new_tracks.add(track)

    update_new_additions_playlist(all_new_tracks, vc=vc)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        filename="logs/refresh.log",
    )

    socketio = SocketIO(VOLUMIO_URL, SOCKETIO_PORT)
    vc = VolumioController(socketio)

    new_feed_tracks = find_candidate_tracks()

    playlist_patterns = json.loads(PLAYLIST_PATTERN_PATH.read_text())
    update_playlists(new_feed_tracks, playlist_patterns=playlist_patterns, vc=vc)

    logs = STATE_LOG_PATH.read_text().splitlines()
    track_progress = extract_progress(logs)

    generate_html_files(vc=vc, track_progress=track_progress)


if __name__ == "__main__":
    main()
