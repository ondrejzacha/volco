import json
import logging
from collections import Counter
from collections.abc import Collection, Mapping
from functools import partial

import jinja2
from socketIO_client import SocketIO

from volco.controller import VolumioController
from volco.models import ListItem
from volco.nts_client import fetch_nts_tracks
from volco.renderer import extract_progress, render_index_file, render_playlist_page
from volco.scraper import browse_tracks, stop_on_overlap

from .constants import (
    CANDIDATE_TRACKS_PATH,
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
    TRACK_PROGRESS_PATH,
    TRACK_SOURCES,
    VOLUMIO_URL,
)

logger = logging.getLogger(__name__)


def remove_playlist_duplicates(playlist: str, controller: VolumioController) -> None:
    playlist_tracks = browse_tracks(f"playlists/{playlist}", vc=controller)

    track_counter = Counter(playlist_tracks)
    for track, count in track_counter.items():
        for _ in range(count - 1):
            logger.info(f"Removing {track.title} from playlist {playlist}.")
            controller.remove_from_playlist(
                playlist, service=track.service, uri=track.uri
            )


def filter_tracks(
    tracks: Collection[ListItem], patterns: Collection[str]
) -> list[ListItem]:
    return [
        track
        for track in tracks
        if any(pattern in track.title.lower() for pattern in patterns)
    ]


def update_new_additions_playlist(
    tracks: Collection[ListItem], vc: VolumioController
) -> None:
    new_tracks = list(tracks)[:N_LATEST]
    current_tracks = browse_tracks(f"playlists/{LATEST_50_NAME}", vc=vc)

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
    track_progress: Mapping[str, int] | None = None,
) -> None:
    logger.info("Generating HTML pages for playlists.")

    loader = jinja2.FileSystemLoader(TEMPLATE_DIR)
    environment = jinja2.Environment(loader=loader)
    template = environment.get_template(PLAYLIST_TEMPLATE_HTML)

    playlists = vc.list_playlists()

    playlist_files: dict[str, str] = {}
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


def find_candidate_tracks(vc: VolumioController) -> list[ListItem]:
    existing_tracks = browse_tracks(f"playlists/{LATEST_50_NAME}", vc=vc)
    logger.info(
        f"find_candidate_tracks: {len(existing_tracks)} existing tracks in '{LATEST_50_NAME}'"
    )
    if existing_tracks:
        logger.debug(
            f"find_candidate_tracks: first existing track = {existing_tracks[0].title!r}, "
            f"last = {existing_tracks[-1].title!r}"
        )

    stop_condition = partial(
        stop_on_overlap, existing_tracks=existing_tracks, min_overlap=5
    )

    all_tracks: list[ListItem] = []
    tracks_by_source: list[dict] = []
    for track_source in TRACK_SOURCES:
        logger.info(f"find_candidate_tracks: scraping source {track_source!r}")
        source_tracks = browse_tracks(track_source, stop_condition=stop_condition, vc=vc)
        logger.info(
            f"find_candidate_tracks: got {len(source_tracks)} tracks from {track_source!r}"
        )
        all_tracks += source_tracks
        tracks_by_source.extend(
            {"source": track_source, "uri": t.stripped_uri, "title": t.title}
            for t in source_tracks
        )

    logger.info(f"find_candidate_tracks: {len(all_tracks)} candidate tracks total")

    CANDIDATE_TRACKS_PATH.write_text(json.dumps(tracks_by_source, indent=2))
    logger.info(f"find_candidate_tracks: wrote candidate tracks to {CANDIDATE_TRACKS_PATH}")

    return all_tracks


def find_candidate_tracks_nts(vc: VolumioController) -> list[ListItem]:
    """
    Alternative to find_candidate_tracks() that uses the NTS API + SC oEmbed
    instead of the Volumio SC plugin (which gets 403s from the SC API).
    """
    existing_tracks = browse_tracks(f"playlists/{LATEST_50_NAME}", vc=vc)
    logger.info(
        f"find_candidate_tracks_nts: {len(existing_tracks)} existing tracks in '{LATEST_50_NAME}'"
    )

    existing_uris = {t.stripped_uri for t in existing_tracks}
    all_tracks = fetch_nts_tracks(existing_uris=existing_uris, min_overlap=5)
    logger.info(f"find_candidate_tracks_nts: {len(all_tracks)} new candidate tracks")

    tracks_by_source = [
        {"source": "nts-api", "uri": t.stripped_uri, "title": t.title}
        for t in all_tracks
    ]
    CANDIDATE_TRACKS_PATH.write_text(json.dumps(tracks_by_source, indent=2))
    logger.info(
        f"find_candidate_tracks_nts: wrote candidate tracks to {CANDIDATE_TRACKS_PATH}"
    )

    return all_tracks


def update_playlists(
    new_feed_tracks: Collection[ListItem],
    playlist_patterns: Mapping[str, Collection[str]],
    vc: VolumioController,
) -> None:
    all_new_tracks: set[ListItem] = set()

    logger.info(
        f"update_playlists: {len(new_feed_tracks)} candidate tracks, "
        f"{len(playlist_patterns)} playlists to update"
    )

    for playlist, patterns in playlist_patterns.items():
        logger.info(f"Handling playlist `{playlist}` (patterns={list(patterns)})")
        current_tracks = browse_tracks(f"playlists/{playlist}", vc=vc)
        current_uris = set(track.stripped_uri for track in current_tracks)
        matching_tracks = filter_tracks(new_feed_tracks, patterns)
        logger.info(
            f"Playlist `{playlist}`: {len(current_tracks)} existing tracks, "
            f"{len(matching_tracks)} candidates match patterns"
        )

        added = 0
        skipped = 0
        for track in matching_tracks:
            if track.stripped_uri in current_uris:
                logger.debug(
                    f"Skipping track `{track.title}` as "
                    f"it already is in playlist `{playlist}`."
                )
                skipped += 1
                continue

            logger.info(f"Adding track `{track.title}` to playlist `{playlist}`.")
            vc.add_to_playlist(playlist, service=track.service, uri=track.stripped_uri)
            all_new_tracks.add(track)
            added += 1

        logger.info(
            f"Playlist `{playlist}`: added {added} new tracks, skipped {skipped} duplicates"
        )

    logger.info(f"update_playlists: {len(all_new_tracks)} unique new tracks across all playlists")
    update_new_additions_playlist(all_new_tracks, vc=vc)


def main(update_tracks=True):
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/refresh.log"),
        ],
    )

    with SocketIO(VOLUMIO_URL, SOCKETIO_PORT) as socketio:
        vc = VolumioController(socketio)

        if update_tracks:
            new_feed_tracks = find_candidate_tracks(vc)

            playlist_patterns = json.loads(PLAYLIST_PATTERN_PATH.read_text())
            update_playlists(
                new_feed_tracks, playlist_patterns=playlist_patterns, vc=vc
            )

        STATE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        TRACK_PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)

        logs = (
            STATE_LOG_PATH.read_text().splitlines() if STATE_LOG_PATH.exists() else []
        )
        track_progress = extract_progress(logs)
        TRACK_PROGRESS_PATH.write_text(json.dumps(track_progress))

        generate_html_files(vc=vc, track_progress=track_progress)


if __name__ == "__main__":
    main()
