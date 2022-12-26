from typing import Dict, List

import httpx
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from socketIO_client import SocketIO
from starlette.routing import Mount

from .constants import ALL_PLAYLISTS, SOCKETIO_PORT, VOLUMIO_URL
from .controller import VolumioController
from .scraper import strip_name

app = FastAPI(
    routes=[
        Mount(
            "/playlists",
            app=StaticFiles(directory="static/playlists"),
            name="playlists",
        )
    ]
)

templates = Jinja2Templates(directory="templates")
socketio = SocketIO(VOLUMIO_URL, SOCKETIO_PORT)
vc = VolumioController(socketio)

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
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "playlists": playlist_urls, "volumio_url": VOLUMIO_URL},
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
    r = await client.post(
        f"http://{VOLUMIO_URL}/api/v1/replaceAndPlay",
        json={"item": {"uri": uri, "service": service}},
    )
    return r.json()


# (volumio list)
@app.post("/playlist/{playlist}/add")
async def add_to_playlist(
    playlist: str, uri: str = Form(), service: str = Form()  # noqa: B008
):
    return vc.add_to_playlist(playlist=playlist, service=service, uri=uri)


@app.post("/playlist/{playlist}/remove")
async def remove_from_playlist(
    playlist: str, uri: str = Form(), service: str = Form()  # noqa: B008
):
    return vc.remove_from_playlist(playlist=playlist, service=service, uri=uri)


@app.get("/playlist/{playlist}")
async def list_tracks(playlist: str):
    # TODO: smarter parsing
    return vc.list_tracks(playlist=playlist).navigation.lists[0]["items"]
