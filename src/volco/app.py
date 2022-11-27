from typing import Dict
from fastapi import FastAPI, Request, Form
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .volumio_controller import VolumioController, TrackSpec
from socketIO_client import SocketIO


app = FastAPI()

socketio = SocketIO("192.168.2.22", 3000)
vc = VolumioController(socketio)

# app.mount("/static", StaticFiles(directory="static"), name="static")


# templates = Jinja2Templates(directory="templates")


# @app.get("/", response_class=HTMLResponse)
# async def read_item(request: Request, id: str):
#     return templates.TemplateResponse("index.html", {"request": request, "id": id})


class AnyData(BaseModel):
    __root__: Dict[str, str]


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
async def play_track(uri: str = Form(), service: str = Form()):
    return vc.play_track(track_spec=TrackSpec(uri=uri, service=service))


@app.post("/queue")
async def queue_track(track_spec: TrackSpec):
    return vc.queue_track(track_spec=track_spec)


# @app.post("/playlist/{playlist}/add")
# async def add_to_playlist(track_spec: TrackSpec, playlist: str):
#     return vc.add_to_playlist(playlist=playlist, track_spec=track_spec)


@app.post("/playlist/{playlist}/add")
async def add_to_playlist(playlist: str, uri: str = Form(), service: str = Form()):
    return vc.add_to_playlist(
        playlist=playlist, track_spec=TrackSpec(service=service, uri=uri)
    )


@app.post("/playlist/{playlist}/remove")
async def remove_from_playlist(playlist: str, uri: str = Form(), service: str = Form()):
    return vc.remove_from_playlist(
        playlist=playlist, track_spec=TrackSpec(service=service, uri=uri)
    )


@app.get("/playlist/{playlist}")
async def list_tracks(playlist: str):
    return vc.list_tracks(playlist=playlist).navigation.lists[0]["items"]


# @app.post("/test2")
# async def test(any_data: AnyData):
#     print(any_data)
#     return any_data

# @app.post("/test")
# async def test(request: Request):
#     form = await request.form()
#     print(form)
#     return form
