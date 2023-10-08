"""Retrieve SoundCloud client ID.

Adapted from
https://github.com/patrickkfkan/soundcloud-fetch/blob/3cca5ead28bd84d59a1da7fd930a9917f623318b/src/lib/utils/SoundCloudKey.ts  # noqa: E501
https://github.com/Tenpi/soundcloud.ts/blob/3cd9b864412e485aa7a8c3885d0695cc10f3485e/API.ts  # noqa: E501
"""
import re

import httpx

WEB_URL = "https://soundcloud.com"
MOBILE_URL = "https://m.soundcloud.com"

JS_SCRIPT_PATTERN = (
    r'((?!<script.*?src=")https?:\/\/(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}'
    r"\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&//=]*\.js)(?=.*?>))"
)
CLIENT_ID_PATTERN_WEB = r'[{,]client_id:"(\w+)"'
CLIENT_ID_PATTERN_MOBILE = r'"clientId":"(\w+?)"'
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5_1 like Mac OS X) AppleWebKit/"
        "605.1.15 (KHTML, like Gecko) CriOS/99.0.4844.47 Mobile/15E148 Safari/604.1"
    )
}


async def get_client_id(client: httpx.AsyncClient) -> str:
    try:
        return await get_client_id_web(client)
    except RuntimeError:
        return await get_client_id_mobile(client)


async def get_client_id_web(client: httpx.AsyncClient) -> str:
    response = await client.get(WEB_URL)

    script_url_matches = list(re.finditer(JS_SCRIPT_PATTERN, response.text))

    if not script_url_matches:
        raise RuntimeError("Could not find script URLs")

    for script_url_match in script_url_matches:
        url = script_url_match.group()
        response = await client.get(url)

        client_id_match = re.search(CLIENT_ID_PATTERN_WEB, response.text)
        if not client_id_match:
            continue
        client_id = client_id_match.group(1)

        return client_id

    raise RuntimeError("Could not find client ID in script URLs")


async def get_client_id_mobile(client: httpx.AsyncClient) -> str:
    request = httpx.Request("GET", MOBILE_URL, headers=HEADERS)
    response = await client.send(request)

    client_id_match = re.search(CLIENT_ID_PATTERN_MOBILE, response.text)
    if not client_id_match:
        raise RuntimeError("Could not find client ID")
    client_id = client_id_match.group(1)
    
    return client_id
