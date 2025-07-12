import datetime
import re

from pydantic import BaseModel, Extra


class UriItem(BaseModel):
    uri: str


class ListItem(BaseModel):
    service: str
    type: str
    title: str
    uri: str
    duration: int | None = None
    album: str | None = None
    artist: str | None = None
    albumart: str | None = None
    year: str | int | None = None
    icon: str | None = None

    def __hash__(self):
        return hash(self.service + self.uri)

    @property
    def stripped_uri(self):
        return strip_uri(self.uri)

    def strip_mixcloud_uri(self):
        return


def strip_uri(uri):
    if uri is None:
        return None
    if uri.startswith("mixcloud"):
        return re.sub(
            r"^(mixcloud/)(.+)?(cloudcast@cloudcastId=[^@]+)(@.+)?$",
            r"\1\3",
            uri,
        )
    if uri.startswith("soundcloud"):
        return re.sub(r"^(soundcloud/)(.+)?(track@trackId=[^@]+)(@.+)?$", r"\1\3", uri)
    return uri


class ListContainer(BaseModel):
    title: str | None = None
    availableListViews: list[str]
    items: list[ListItem]


class Navigation(BaseModel):
    prev: UriItem
    lists: list[ListContainer]
    info: ListItem


class BrowseResponse(BaseModel):
    navigation: Navigation


class VolumioResponse(BaseModel):
    success: bool
    reason: str | None


class ResultList(BaseModel):
    __root__: list[str]


class ToastMessage(BaseModel):
    message: str
    title: str
    type: str


class State(BaseModel, extra=Extra.ignore):
    status: str
    service: str
    uri: str
    title: str
    artist: str
    seek: int
    duration: int


class StateLog(BaseModel):
    ts: datetime.datetime
    state: State


class PlaylistRules(BaseModel):
    __root__: dict[str, list[str]]


class PlayerResponse(BaseModel):
    time: int
    response: str


class MixcloudResult(BaseModel):
    key: str
    url: str
    name: str
