from __future__ import annotations

import json
import logging
from collections.abc import Callable, Collection
from functools import partial
from typing import TYPE_CHECKING

import httpx

from .constants import VOLUMIO_API_URL
from .models import BrowseResponse, ListItem

if TYPE_CHECKING:
    from .controller import VolumioController

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
    logger.debug(
        f"stop_on_overlap: {len(overlap)} overlap out of {len(tracks)} fetched "
        f"vs {len(existing_tracks)} existing (threshold={min_overlap})"
    )
    return len(overlap) >= min_overlap


def _fetch_browse_response(uri: str, vc: VolumioController | None) -> BrowseResponse | None:
    if vc is not None:
        return vc.browse(uri)

    r = httpx.get(f"http://{VOLUMIO_API_URL}/api/v1/browse?uri={uri}")
    browse_json = r.json()
    logger.info(
        # Full raw JSON from the Volumio SoundCloud plugin browse API (HTTP path)
        f"_fetch_browse_response({uri!r}) raw HTTP response:\n{json.dumps(browse_json, indent=2)}"
    )
    try:
        return BrowseResponse.parse_obj(browse_json)
    except Exception:
        if isinstance(browse_json, dict) and browse_json.get("error") == "No Result":
            return None
        logger.error(
            f"Failed to parse browse response for uri={uri}. "
            f"Keys: {list(browse_json.keys()) if isinstance(browse_json, dict) else type(browse_json)}"
        )
        return None


def browse_tracks(
    uri: str,
    stop_condition: StopCondition | None = None,
    vc: VolumioController | None = None,
) -> list[ListItem]:
    if stop_condition is None:
        stop_condition = partial(stop_on_max_tracks, max_tracks=5000)

    all_tracks: list[ListItem] = []
    page_num = 0
    original_uri = uri

    logger.info(f"browse_tracks: starting URI={uri}")

    while not stop_condition(all_tracks):
        page_num += 1
        logger.debug(f"browse_tracks [{original_uri}]: fetching page {page_num} (uri={uri})")

        browse_response = _fetch_browse_response(uri, vc)
        if browse_response is None:
            logger.info(
                f"browse_tracks [{original_uri}]: no more results after {page_num - 1} pages, "
                f"{len(all_tracks)} tracks total"
            )
            break

        logger.debug(
            f"browse_tracks [{original_uri}]: page {page_num} response has "
            f"{len(browse_response.navigation.lists)} list(s): "
            + ", ".join(
                f"[{i}] title={lst.title!r} items={len(lst.items)} "
                f"types={list({it.type for it in lst.items})}"
                for i, lst in enumerate(browse_response.navigation.lists)
            )
        )
        list_items = browse_response.navigation.lists[-1].items  # TODO: fix lists[-1]

        page_tracks = 0
        skipped_duplicates = 0
        for item in list_items:
            if item.type not in {"song", "folder"} or item in all_tracks:
                if item.type in {"song", "folder"}:
                    skipped_duplicates += 1
                continue
            all_tracks.append(item)
            page_tracks += 1

        logger.info(
            f"browse_tracks [{original_uri}]: page {page_num} — "
            f"{page_tracks} new tracks, {skipped_duplicates} dupes skipped, "
            f"{len(all_tracks)} total: {[t.title for t in all_tracks[-page_tracks:]] if page_tracks else []}"
        )

        next_page = next(
            (
                item
                for item in list_items
                if item.type in {"mixcloudNextPageItem", "soundcloudNextPageItem"}
                or (item.type == "item-no-menu" and "pageRef" in (item.uri or ""))
            ),
            None,
        )
        if next_page is None:
            logger.info(
                f"browse_tracks [{original_uri}]: no more pages after {page_num} pages, "
                f"{len(all_tracks)} tracks total"
            )
            break

        logger.debug(f"browse_tracks [{original_uri}]: next page URI={next_page.uri}")
        uri = next_page.uri
    else:
        logger.info(
            f"browse_tracks [{original_uri}]: stop condition triggered after "
            f"{page_num} pages, {len(all_tracks)} tracks collected"
        )

    return all_tracks
