import logging
from datetime import datetime
from typing import Dict, Iterable, Mapping, Sequence

import jinja2
import pydantic

from volco.models import ListItem, StateLog, strip_uri

logger = logging.getLogger(__name__)


def extract_progress(logs: Iterable[str]) -> Dict[str, int]:
    max_seek_positions: Dict[str, int] = {}
    durations: Dict[str, int] = {}

    # Extract max seek position for each URI
    for line in logs:
        try:
            log = StateLog.parse_raw(line)
        except pydantic.error_wrappers.ValidationError:
            continue

        if log.state.service not in {"mixcloud", "soundcloud"}:
            continue

        uri = strip_uri(log.state.uri)
        max_seek_positions[uri] = max(log.state.seek, max_seek_positions.get(uri, 0))
        durations[uri] = log.state.duration

    # Calculate progress percentage
    progress: Dict[str, int] = {}
    for uri, duration in durations.items():
        # "Seek" is in microseconds, duration in seconds
        max_seek_seconds = max_seek_positions[uri] / 1000

        if duration == 0:
            logger.warning(
                f"Found track log with zero duration for URI {uri}. Skipping."
            )
            continue

        progress[uri] = int(round(max_seek_seconds / duration, 1) * 100)

    return progress


def render_playlist_page(
    title: str,
    tracks: Sequence[ListItem],
    track_progress: Mapping[str, int],
    template: jinja2.Template,
) -> str:
    track_data = [
        {**track.dict(), "progress": track_progress.get(track.stripped_uri, 0)}
        for track in tracks
    ]

    rendered = template.render(
        {
            "playlist_name": title,
            "tracks": track_data,
            "ts": datetime.now(),
        }
    )

    return rendered


def render_index_file(
    playlist_files: Mapping[str, str],
    template: jinja2.Template,
) -> str:
    playlist_urls = [
        {"name": playlist, "url": f"/playlists/{filename}"}
        for playlist, filename in playlist_files.items()
    ]

    rendered = template.render({"playlists": playlist_urls})

    return rendered
