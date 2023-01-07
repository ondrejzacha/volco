from typing import Dict, List

import httpx
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from socketIO_client import SocketIO
from starlette.routing import Mount

from .constants import ALL_PLAYLISTS, VOLUMIO_API_URL
from .controller import VolumioController
from .scraper import strip_name


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
    ]
)
templates = Jinja2Templates(directory="templates")
playlist_urls: List[Dict[str, str]] = []


async def get_client():
    # create a new client for each request
    async with httpx.AsyncClient() as client:
        # yield the client to the endpoint function
        yield client
        # close the client when the request is done


@app.on_event("startup")
async def startup_event():
    global playlist_urls
    # TODO: get from volumio on startup
    playlist_urls.clear()
    playlist_urls += [
        {"name": playlist, "url": f"/playlists/{strip_name(playlist)}.html"}
        for playlist in ALL_PLAYLISTS
    ]


@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    # Index needs "public" URL as it needs to call API from client side
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "playlists": playlist_urls,
        },
    )


@app.get("/health")
async def get_health():
    return "OK"


@app.post("/playback/replace")
async def play_track(
    uri: str = Form(),  # noqa: B008
    service: str = Form(),  # noqa: B008
    client: httpx.AsyncClient = Depends(get_client),  # noqa: B008
) -> Dict[str, str]:
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
) -> Dict[str, str]:
    # This needs localhost as the call is made on server side
    r = await client.get(
        f"http://{VOLUMIO_API_URL}/api/v1/commands/?cmd=play",
    )
    return r.json()


@app.post("/playback/pause")
async def pause(
    client: httpx.AsyncClient = Depends(get_client),  # noqa: B008
) -> Dict[str, str]:
    # This needs localhost as the call is made on server side
    r = await client.get(
        f"http://{VOLUMIO_API_URL}/api/v1/commands/?cmd=pause",
    )
    return r.json()


@app.get("/playback/status")
async def get_status(
    client: httpx.AsyncClient = Depends(get_client),  # noqa: B008
) -> Dict[str, str]:
    # This needs localhost as the call is made on server side
    r = await client.get(
        f"http://{VOLUMIO_API_URL}/api/v1/getState",
    )
    return r.json()
