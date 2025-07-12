from collections.abc import Callable
from typing import Any

from pydantic import BaseModel
from socketIO_client import SocketIO

from .models import BrowseResponse, ListItem, ResultList, ToastMessage, VolumioResponse


class VolumioController:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.responses: dict[str, Any] = {}

    def _create_callback(self, message: str) -> Callable[[Any], None]:
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
        message_in: str | None = None,
        data: Any = None,
        response_model: BaseModel | None = None,
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
            return response_model.parse_obj(response[0])
        return response

    def list_playlists(self) -> list[str]:
        result_obj: ResultList = self.call(
            message_out="listPlaylist",
            message_in="pushListPlaylist",
            response_model=ResultList,
        )
        playlists = result_obj.__root__
        return playlists

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
    # def queue_track(self, track_spec: TrackSpec) -> ToastMessage:
    #     return self.call(
    #         message_out="addToQueue",
    #         data=track_spec.dict(),
    #         response_model=ToastMessage,
    #     )

    # also volumio REST API
    # TODO: other lists
    def list_tracks(self, playlist: str) -> list[ListItem]:
        result_obj: BrowseResponse = self.call(
            message_out="browseLibrary",
            message_in="pushBrowseLibrary",
            data={"uri": f"playlists/{playlist}"},
            response_model=BrowseResponse,
        )
        tracks = result_obj.navigation.lists[-1].items
        return tracks

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
