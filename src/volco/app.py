import httpx
from fastapi import FastAPI, Form, Request
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

playlist_urls: list[dict[str, str]] = []


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
        "index.html", {"request": request, "playlists": playlist_urls}
    )


@app.get("/health")
async def get_health():
    return "OK"


@app.get("/state")
async def get_state():
    return vc.get_state()[0]


@app.post("/playback/start")
async def play():
    return vc.play()


@app.post("/playback/pause")
async def pause():
    return vc.pause()


@app.post("/playback/replace")
async def play_track(uri: str = Form(), service: str = Form()):  # noqa: B008
    """Used to accept form data input."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"http://{VOLUMIO_URL}/api/v1/replaceAndPlay",
            json={"item": {"uri": uri, "service": service}},
        )


# @app.post("/queue")
# async def queue_track(track_spec: TrackSpec):
#     return vc.queue_track(track_spec=track_spec)


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
