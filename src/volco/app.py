from typing import Dict

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from socketIO_client import SocketIO

from .constants import ALL_PLAYLISTS, SOCKETIO_PORT, VOLUMIO_URL
from .volumio_controller import TrackSpec, VolumioController
from .volumio_scraper import strip_name

app = FastAPI()

socketio = SocketIO(VOLUMIO_URL, SOCKETIO_PORT)
vc = VolumioController(socketio)

# TODO: mount as route?
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class AnyData(BaseModel):
    __root__: Dict[str, str]


# TODO
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    # TODO: get from volumio on startup

    playlist_urls = [
        {"name": playlist, "url": f"/static/playlists/{strip_name(playlist)}.html"}
        for playlist in ALL_PLAYLISTS
    ]
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


# @app.post("/playback/replace")
# async def play_track(uri: str = Form(), service: str = Form()):  # noqa: B008
#     return vc.play_track(track_spec=TrackSpec(uri=uri, service=service))


# @app.post("/queue")
# async def queue_track(track_spec: TrackSpec):
#     return vc.queue_track(track_spec=track_spec)


# @app.post("/playlist/{playlist}/add")
# async def add_to_playlist(track_spec: TrackSpec, playlist: str):
#     return vc.add_to_playlist(playlist=playlist, track_spec=track_spec)

# (volumio list)
@app.post("/playlist/{playlist}/add")
async def add_to_playlist(
    playlist: str, uri: str = Form(), service: str = Form()  # noqa: B008
):
    return vc.add_to_playlist(
        playlist=playlist, track_spec=TrackSpec(service=service, uri=uri)
    )


@app.post("/playlist/{playlist}/remove")
async def remove_from_playlist(
    playlist: str, uri: str = Form(), service: str = Form()  # noqa: B008
):
    return vc.remove_from_playlist(
        playlist=playlist, track_spec=TrackSpec(service=service, uri=uri)
    )


@app.get("/playlist/{playlist}")
async def list_tracks(playlist: str):
    return vc.list_tracks(playlist=playlist).navigation.lists[0]["items"]
