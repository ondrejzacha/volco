import logging
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel
from socketIO_client import SocketIO

from .models import BrowseResponse, ListItem, ResultList, ToastMessage, VolumioResponse

logger = logging.getLogger(__name__)


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

    def _get_response(self, message: str, timeout: float = 30.0) -> tuple | None:
        elapsed = 0.0
        interval = 0.5
        while elapsed < timeout:
            self.socketio.wait(interval)
            elapsed += interval
            response = self.responses.pop(message, None)
            if response is not None:
                return response
        return None

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

    def browse(self, uri: str) -> BrowseResponse | None:
        response = self._get_raw_browse(uri)
        if response is None:
            logger.warning(f"browse({uri!r}): no response received (timeout?)")
            return None
        raw = response[0]
        try:
            return BrowseResponse.parse_obj(raw)
        except Exception:
            error = raw.get("error") if isinstance(raw, dict) else None
            if error == "No Result":
                return None
            logger.error(
                f"browse({uri!r}): failed to parse response. "
                f"Keys: {list(raw.keys()) if isinstance(raw, dict) else type(raw)}"
            )
            return None

    def _get_raw_browse(self, uri: str) -> tuple | None:
        self._listen_for("pushBrowseLibrary")
        self._emit("browseLibrary", {"uri": uri})
        return self._get_response("pushBrowseLibrary")

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
