from socketIO_client import SocketIO
from pydantic import BaseModel

from typing import Callable, List, Any, Dict


class TrackSpec(BaseModel):
    service: str
    uri: str


class VolumioResponse(BaseModel):
    success: bool
    reason: str | None


class ResultList(BaseModel):
    __root__: List[str]


class ToastMessage(BaseModel):
    message: str
    title: str
    type: str


class VolumioController:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.responses: Dict[str, Any] = {}

    def _create_callback(self, message: str) -> "Callable[[Any], None]":
        def inner(*args):
            self.responses[message] = args

        return inner

    def _listen_for(self, message: str):
        self.socketio.once(message, self._create_callback(message))

    def _emit(self, *args):
        self.socketio.emit(*args)

    def _get_response(self, message: str) -> tuple:
        self.socketio.wait(0.5)
        response = self.responses.get(message)
        return response

    def call(
        self,
        message_out: str,
        message_in: str = None,
        data: Any = None,
        response_model: BaseModel = None,
    ) -> BaseModel | tuple | None:
        if message_in:
            self._listen_for(message_in)

        if data is None:
            self._emit(message_out)
        else:
            self._emit(message_out, data)

        if not message_in:
            return

        response = self._get_response(message_in)
        if response_model is not None:
            print(response)
            return response_model.parse_obj(response[0])
        return response

    def list_playlists(self) -> ResultList:
        return self.call(
            message_out="listPlaylist",
            message_in="pushListPlaylist",
            response_model=ResultList,
        )

    def add_to_playlist(self, playlist: str, track_spec: TrackSpec) -> VolumioResponse:
        return self.call(
            message_out="addToPlaylist",
            message_in="pushToastMessage",
            data={"name": playlist, **track_spec.dict()},
            response_model=ToastMessage,
        )

    def remove_from_playlist(
        self, playlist: str, track_spec: TrackSpec
    ) -> VolumioResponse:
        return self.call(
            message_out="removeFromPlaylist",
            message_in="pushToastMessage",
            data={"name": playlist, "uri": track_spec.uri,},
            response_model=ToastMessage,
        )

    def play(self):
        return self.call(message_out="play")

    def pause(self):
        return self.call(message_out="pause")

    def get_state(self):
        return self.call(message_out="getState", message_in="pushState")

    def list_tracks(self):
        ...

    def create_playlist(self, name: str):
        ...

    def play_track(self, track_spec: TrackSpec):
        return self.call(message_out="replaceAndPlay", data=track_spec.dict(),)

    def queue_track(self, track_spec: TrackSpec):
        return self.call(
            message_out="addToQueue",
            data=track_spec.dict(),
            response_model=ToastMessage,
        )
