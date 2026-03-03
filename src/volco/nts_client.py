"""
Fetch candidate NTS tracks via the NTS API + SoundCloud oEmbed.

This is an alternative to browsing by userId via the Volumio SoundCloud plugin,
which gets 403s from the SC API. Instead we:
  1. Page through https://www.nts.live/api/v2/collections/recently-added
  2. For each episode, resolve the SC URL via SC's unauthenticated oEmbed API
     to extract the numeric trackId.
  3. Build a Volumio-compatible ListItem URI:
       soundcloud/tracks@userId=<NTS_LATEST_USER_ID>/track@trackId=<trackId>
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Collection

import httpx

from .models import ListItem

logger = logging.getLogger(__name__)

NTS_API_BASE = "https://www.nts.live/api/v2"
SC_OEMBED_URL = "https://soundcloud.com/oembed"

# Numeric SC user ID for the NTS Latest account (soundcloud.com/user-202286394-991268468).
# All recent NTS episodes are uploaded to this account.
NTS_LATEST_SC_USER_ID = "995897410"


async def _resolve_sc_track_id(
    sc_url: str, client: httpx.AsyncClient
) -> str | None:
    """Return the numeric SC track ID for a SoundCloud URL, or None on failure."""
    try:
        r = await client.get(SC_OEMBED_URL, params={"url": sc_url, "format": "json"})
        r.raise_for_status()
        data = r.json()
        # oEmbed html contains the track URL, possibly percent-encoded:
        #   url=https%3A%2F%2Fapi.soundcloud.com%2Ftracks%2F<trackId>
        match = re.search(
            r"soundcloud\.com(?:/|%2F)tracks(?:/|%2F)(\d+)",
            data.get("html", ""),
            re.IGNORECASE,
        )
        if match:
            return match.group(1)
        logger.warning(f"_resolve_sc_track_id: no track ID in oEmbed for {sc_url!r}")
    except Exception as exc:
        logger.warning(f"_resolve_sc_track_id: failed for {sc_url!r}: {exc}")
    return None


def _episode_to_list_item(episode: dict, track_id: str) -> ListItem:
    albumart = episode.get("media", {}).get("picture_medium", "") or ""
    uri = f"soundcloud/tracks@userId={NTS_LATEST_SC_USER_ID}/track@trackId={track_id}"
    return ListItem(
        service="soundcloud",
        type="song",
        title=episode["name"],
        artist="NTS",
        albumart=albumart,
        uri=uri,
    )


async def _fetch_nts_tracks_async(
    limit: int,
    existing_uris: Collection[str],
    min_overlap: int,
) -> list[ListItem]:
    """
    Page through the NTS recently-added collection and resolve SC track IDs in
    parallel via oEmbed. Stops early once `min_overlap` already-known tracks
    are encountered (same stop-condition logic as the SC plugin path).
    """
    result: list[ListItem] = []
    offset = 0
    page_size = 12  # NTS API caps at 12 results per page regardless of limit param
    overlap_count = 0

    async with httpx.AsyncClient(timeout=15.0) as client:
        while len(result) < limit:
            logger.info(
                f"fetch_nts_tracks: requesting NTS API offset={offset} page_size={page_size}"
            )
            r = await client.get(
                f"{NTS_API_BASE}/collections/recently-added",
                params={"limit": page_size, "offset": offset},
            )
            if r.status_code in (400, 422):
                logger.info(
                    f"fetch_nts_tracks: NTS API returned {r.status_code} at offset={offset}, stopping"
                )
                break
            r.raise_for_status()
            data = r.json()
            episodes = data["results"]
            if not episodes:
                logger.info("fetch_nts_tracks: no more episodes from NTS API")
                break

            # Filter to episodes that have a SC audio source
            sc_episodes = [
                (ep, next(a["url"] for a in ep["audio_sources"] if a["source"] == "soundcloud"))
                for ep in episodes
                if any(a["source"] == "soundcloud" for a in ep.get("audio_sources", []))
            ]
            logger.info(
                f"fetch_nts_tracks: {len(sc_episodes)}/{len(episodes)} episodes have SC links"
            )

            # Resolve all track IDs in parallel
            track_ids = await asyncio.gather(
                *[_resolve_sc_track_id(sc_url, client) for _, sc_url in sc_episodes]
            )

            page_new = 0
            for (episode, _), track_id in zip(sc_episodes, track_ids):
                if track_id is None:
                    continue
                item = _episode_to_list_item(episode, track_id)
                if item.stripped_uri in existing_uris:
                    overlap_count += 1
                    logger.debug(
                        f"fetch_nts_tracks: overlap #{overlap_count} — {item.title!r}"
                    )
                    if overlap_count >= min_overlap:
                        logger.info(
                            f"fetch_nts_tracks: reached {min_overlap} overlaps, stopping early"
                        )
                        return result
                else:
                    result.append(item)
                    page_new += 1

            logger.info(
                f"fetch_nts_tracks: offset={offset} — {page_new} new tracks, "
                f"{len(result)} total so far, {overlap_count} overlaps"
            )
            offset += page_size

    return result


def fetch_nts_tracks(
    existing_uris: Collection[str] | None = None,
    limit: int = 200,
    min_overlap: int = 5,
) -> list[ListItem]:
    """
    Synchronous entry point. Returns new NTS tracks not already in `existing_uris`.
    """
    return asyncio.run(
        _fetch_nts_tracks_async(
            limit=limit,
            existing_uris=existing_uris or set(),
            min_overlap=min_overlap,
        )
    )
