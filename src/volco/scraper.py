import logging
from functools import partial
from typing import Callable, Collection, List, Optional

import httpx

from .constants import VOLUMIO_API_URL
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

    all_tracks: List[ListItem] = []

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

        logger.debug(".")
        uri = next_page.uri

    return all_tracks
