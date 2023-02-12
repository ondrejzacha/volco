"""Tracklist link extraction

Very specific module to find links to NTS show tracklists
for currenly playing tracks.
"""

import re
from typing import Optional

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
) -> Optional[str]:
    """Get NTS tracklist URL for current track"""
    r = await client.get(
        f"http://{VOLUMIO_API_URL}/api/v1/getState",
    )
    state = State.parse_obj(r.json())
    if state.artist != "NTS Radio":
        return None

    mixcloud_page = await get_mixcloud_page(state.title, client)
    if mixcloud_page is None:
        return None

    nts_link = await get_nts_link(mixcloud_page, client)

    return nts_link


async def get_mixcloud_page(name: str, client: httpx.AsyncClient) -> Optional[str]:
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


async def get_nts_link(mixcloud_url: str, client: httpx.AsyncClient) -> Optional[str]:
    """Find a link to NTS show episode page on Mixcloud track page"""
    api_url = mixcloud_url.replace("www.mixcloud", "api.mixcloud")
    r = await client.get(api_url)

    if r.status_code != 200:
        return None

    description = r.json()["description"]
    nts_link = next(
        iter(re.findall(r"https://www.nts.live[/\w\-]+", description)), None
    )

    return nts_link
