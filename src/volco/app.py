import json
from pathlib import Path

import httpx
import pydantic
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.routing import Mount

from volco.constants import (
    INDEX_PATH,
    PLAYLIST_PATTERN_PATH,
    TEMPLATE_DIR,
    VOLUMIO_API_URL,
)
from volco.models import PlayerResponse, PlaylistRules, State
from volco.tracklist import get_tracklist_link

Path("static/playlists").mkdir(parents=True, exist_ok=True)
Path("logs").mkdir(parents=True, exist_ok=True)
Path("static").mkdir(parents=True, exist_ok=True)

app = FastAPI(
    routes=[
        Mount(
            "/playlists",
            app=StaticFiles(directory="static/playlists"),
            name="playlists",
        ),
        Mount(
            "/logs",
            app=StaticFiles(directory="logs"),
            name="logs",
        ),
        Mount(
            "/static",
            app=StaticFiles(directory="static"),
            name="static",
        ),
    ]
)
templates = Jinja2Templates(directory=TEMPLATE_DIR)
index_html = INDEX_PATH.read_text()


async def get_client():
    # create a new client for each request
    async with httpx.AsyncClient() as client:
        # yield the client to the endpoint function
        yield client
        # close the client when the request is done


@app.get("/", response_class=HTMLResponse)
async def get_index():
    return index_html


@app.get("/patterns", response_class=HTMLResponse)
async def get_patterns(request: Request):
    current_patterns = (
        PLAYLIST_PATTERN_PATH.read_text() if PLAYLIST_PATTERN_PATH.exists() else "{}"
    )
    return templates.TemplateResponse(
        "patterns.html",
        {
            "request": request,
            "current_patterns": current_patterns,
        },
    )


@app.post("/patterns/submit")
async def submit_patterns(
    playlist_rules: str = Form(),
) -> str:
    try:
        parsed_rules = PlaylistRules.parse_raw(playlist_rules)
    except (json.JSONDecodeError, pydantic.error_wrappers.ValidationError) as e:
        raise HTTPException(
            status_code=400, detail=f"Wrong format. Full message: {e}."
        ) from e

    new_rules_json = json.dumps(parsed_rules.__root__, indent=2)
    PLAYLIST_PATTERN_PATH.write_text(new_rules_json)

    return "Playlist rules updated."


@app.get("/health")
async def get_health():
    return "OK"


@app.post("/playback/replace")
async def play_track(
    uri: str = Form(),
    service: str = Form(),
    client: httpx.AsyncClient = Depends(get_client),  # noqa: B008
) -> dict[str, str]:
    """Used to accept form data input."""
    # This needs localhost as the call is made on server side
    r = await client.post(
        f"http://{VOLUMIO_API_URL}/api/v1/replaceAndPlay",
        json={"item": {"uri": uri, "service": service}},
    )
    return r.json()


# play, post, status redirected to stay on the same port (volumio API runs on port 3000)
@app.post("/playback/play")
async def play(
    client: httpx.AsyncClient = Depends(get_client),  # noqa: B008
) -> PlayerResponse:
    # This needs localhost as the call is made on server side
    r = await client.get(
        f"http://{VOLUMIO_API_URL}/api/v1/commands/?cmd=play",
    )
    return PlayerResponse.parse_obj(r.json())


@app.post("/playback/pause")
async def pause(
    client: httpx.AsyncClient = Depends(get_client),  # noqa: B008
) -> PlayerResponse:
    # This needs localhost as the call is made on server side
    r = await client.get(
        f"http://{VOLUMIO_API_URL}/api/v1/commands/?cmd=pause",
    )
    return PlayerResponse.parse_obj(r.json())


@app.get("/playback/status")
async def get_status(
    client: httpx.AsyncClient = Depends(get_client),  # noqa: B008
) -> State:
    # This needs localhost as the call is made on server side
    r = await client.get(
        f"http://{VOLUMIO_API_URL}/api/v1/getState",
    )
    return State.parse_obj(r.json())


@app.get("/tracklist", response_model=None)
async def get_tracklist(
    client: httpx.AsyncClient = Depends(get_client),  # noqa: B008
) -> RedirectResponse:
    state = await get_status(client)

    if "NTS" not in state.artist:
        raise HTTPException(400, "Not an NTS track")

    tracklist_link = await get_tracklist_link(state, client)
    return RedirectResponse(tracklist_link)
