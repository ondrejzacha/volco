from datetime import datetime
from typing import Dict, Iterable, Mapping, Sequence

import jinja2
from volco.models import ListItem, StateLog, strip_uri


def extract_progress(logs: Iterable[str]) -> Dict[str, int]:
    max_seek_positions: Dict[str, int] = {}
    durations: Dict[str, int] = {}

    # Extract max seek position for each URI
    for line in logs:
        log = StateLog.parse_raw(line)
        uri = strip_uri(log.state.uri)
        max_seek_positions[uri] = max(log.state.seek, max_seek_positions.get(uri, 0))
        durations[uri] = log.state.duration

    # Calculate progress percentage
    progress: Dict[str, float] = {}
    for uri, duration in durations.items():
        # "Seek" is in microseconds, duration in seconds
        max_seek_seconds = max_seek_positions[uri] / 1000
        progress[uri] = round(max_seek_seconds / duration, 1) * 100

    return progress


def render_playlist_page(
    title: str,
    tracks: Sequence[ListItem],
    track_progress: Mapping[str, str],
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
