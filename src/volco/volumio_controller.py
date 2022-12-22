from typing import Any, Callable

from pydantic import BaseModel
from socketIO_client import SocketIO

from .volumio_models import BrowseResponse, ResultList, ToastMessage, VolumioResponse


class VolumioController:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.responses: dict[str, Any] = {}

    def _create_callback(self, message: str) -> "Callable[[Any], None]":
        def inner(*args):
            self.responses[message] = args

        return inner

    def _listen_for(self, message: str):
        self.socketio.once(message, self._create_callback(message))

    def _emit(self, *args):
        self.socketio.emit(*args)

    def _get_response(self, message: str) -> tuple | None:
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
            return None

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

    def add_to_playlist(self, playlist: str, service: str, uri: str) -> ToastMessage:
        return self.call(
            message_out="addToPlaylist",
            message_in="pushToastMessage",
            data={"name": playlist, "service": service, "uri": uri},
            response_model=ToastMessage,
        )

    def remove_from_playlist(
        self, playlist: str, service: str, uri: str
    ) -> ToastMessage:
        return self.call(
            message_out="removeFromPlaylist",
            message_in="pushToastMessage",
            data={"name": playlist, "service": service, "uri": uri},
            response_model=ToastMessage,
        )

    # TODO: use volumio REST API instead
    def play(self):
        return self.call(message_out="play")

    # also volumio REST API
    def pause(self):
        return self.call(message_out="pause")

    # also volumio REST API
    # TODO: model for response?
    def get_state(self):
        return self.call(message_out="getState", message_in="pushState")

    # # also volumio REST API
    # # TODO: figure out response?
    # def play_track(self, track_spec: TrackSpec) -> None:
    #     return self.call(message_out="replaceAndPlay", data=track_spec.dict(),)

    # # also volumio REST API
    # def queue_track(self, track_spec: TrackSpec) -> ToastMessage:
    #     return self.call(
    #         message_out="addToQueue",
    #         data=track_spec.dict(),
    #         response_model=ToastMessage,
    #     )

    # also volumio REST API
    # TODO: other lists
    def list_tracks(self, playlist: str) -> BrowseResponse:
        return self.call(
            message_out="browseLibrary",
            message_in="pushBrowseLibrary",
            data={"uri": f"playlists/{playlist}"},
            response_model=BrowseResponse,
        )

    # Playlists are also created by adding a track to a non-existent playlist
    def create_playlist(self, name: str):
        return self.call(
            message_out="createPlaylist",
            message_in="pushCreatePlaylist",
            data={"name": name},
            response_model=VolumioResponse,
        )

    def delete_playlist(self, name: str):
        return self.call(
            message_out="deletePlaylist",
            message_in="pushDeletePlaylist",
            data={"name": name},
            # response_model=VolumioResponse,
        )
