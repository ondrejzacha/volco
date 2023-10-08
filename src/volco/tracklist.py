"""Tracklist link extraction

Very specific module to find links to NTS show tracklists
for currenly playing tracks.
"""

import re
from typing import Dict, Optional
from urllib.parse import quote_plus

import httpx
from fastapi import HTTPException

from .models import MixcloudResult, State
from .sc_client_id import get_client_id


async def get_tracklist_link(
    state: State,
    client: httpx.AsyncClient,  # noqa: B008
) -> str:
    """Get NTS tracklist URL from given state"""
    if state.uri.startswith("mixcloud"):
        return await get_nts_link_from_mixcloud(state.title, client)
    elif state.uri.startswith("soundcloud"):
        return await get_nts_link_from_soundcloud(state.title, client)
    raise HTTPException(400, "Only SoundCloud and Mixcloud tracks are supported.")


async def get_nts_link_from_soundcloud(name: str, client: httpx.AsyncClient) -> str:
    """Find a link to NTS show episode page via SoundCloud API"""
    client_id = await get_client_id(client)
    api_url = (
        f"https://api-v2.soundcloud.com/"
        f"search?q={quote_plus(name)}&client_id={client_id}"
    )

    r = await client.get(api_url)
    if r.status_code != 200:
        raise HTTPException(404, "Could not get link via SoundCloud API")

    track_results = r.json().get("collection", [])
    first_result: Dict[str, str] = next(iter(track_results), {})
    description = first_result.get("description", "")

    nts_link = _extract_link(description)

    return nts_link


async def get_nts_link_from_mixcloud(name: str, client: httpx.AsyncClient) -> str:
    """Find a link to NTS show episode page on Mixcloud track page"""
    track_url = await _find_mixcloud_track_url(name, client)

    if track_url is None:
        raise HTTPException(404, "Could not find Mixcloud URL")

    api_url = track_url.replace("www.mixcloud", "api.mixcloud")
    r = await client.get(api_url)
    if r.status_code != 200:
        raise HTTPException(404, "Could not get link via Mixcloud API")

    description = r.json()["description"]
    nts_link = _extract_link(description)

    return nts_link


async def _find_mixcloud_track_url(
    name: str, client: httpx.AsyncClient
) -> Optional[str]:
    """Search Mixcloud tracks by title"""
    url = f"https://api.mixcloud.com/search/?q={name}&type=cloudcast"
    r = await client.get(url)
    search_results = [MixcloudResult.parse_obj(obj) for obj in r.json()["data"]]

    # Mixcloud API does not always return an exact match
    matching_urls = (
        sr.url
        for sr in search_results
        if sr.name == name and sr.key.startswith("/NTSRadio")
    )
    return next(
        matching_urls,
        None,
    )


def _extract_link(description: str) -> str:
    """Extract NTS link from track description"""
    link = next(iter(re.findall(r"https://www.nts.live[/\w\-]+", description)), None)
    if not link:
        raise HTTPException(404, "NTS link not found.")
    return link
