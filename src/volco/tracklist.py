"""Tracklist link extraction

Very specific module to find links to NTS show tracklists
for currenly playing tracks.
"""

import os
import re
from typing import Optional
from urllib.parse import quote_plus

import httpx
from pydantic import BaseModel

from .constants import VOLUMIO_API_URL
from .models import State


class MixcloudResult(BaseModel):
    key: str
    url: str
    name: str


async def get_tracklist_link(
    client: httpx.AsyncClient,  # noqa: B008
    sc_client_id: str,
    sc_oauth_token: str,
) -> Optional[str]:
    """Get NTS tracklist URL for current track"""
    r = await client.get(
        f"http://{VOLUMIO_API_URL}/api/v1/getState",
    )
    state = State.parse_obj(r.json())
    if "NTS" not in state.artist:
        return None

    if state.uri.startswith("mixcloud"):
        nts_link = await get_nts_link_from_mixcloud(state.title, client)
    elif state.uri.startswith("soundcloud"):
        nts_link = await get_nts_link_from_soundcloud(
            state.title, client, client_id=sc_client_id, oauth_token=sc_oauth_token
        )
    else:
        return None

    return nts_link


async def get_nts_link_from_soundcloud(
    name: str, client: httpx.AsyncClient, client_id: str, oauth_token: str
) -> Optional[str]:
    """Find a link to NTS show episode page via SoundCloud API"""
    api_url = (
        f"https://api-v2.soundcloud.com/"
        f"search?q={quote_plus(name)}&client_id={client_id}"
    )

    r = await client.get(
        api_url,
        headers={"Authorization": f"OAuth {oauth_token}"},
    )

    if r.status_code != 200:
        return None

    track_results = r.json().get("collection", [])
    first_result = next(iter(track_results), {})
    description = first_result.get("description", "")

    nts_link = _extract_link(description)

    return nts_link


async def get_nts_link_from_mixcloud(
    name: str, client: httpx.AsyncClient
) -> Optional[str]:
    """Find a link to NTS show episode page on Mixcloud track page"""
    track_url = await _find_mixcloud_track_url(name, client)

    if track_url is None:
        return None

    api_url = track_url.replace("www.mixcloud", "api.mixcloud")
    r = await client.get(api_url)
    if r.status_code != 200:
        return None

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


def _extract_link(description: str) -> Optional[str]:
    return next(iter(re.findall(r"https://www.nts.live[/\w\-]+", description)), None)
