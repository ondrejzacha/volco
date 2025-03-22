import datetime
import re
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Extra


class UriItem(BaseModel):
    uri: str


class ListItem(BaseModel):
    service: str
    type: str
    title: str
    uri: str
    duration: Optional[int] = None
    album: Optional[str] = None
    artist: Optional[str] = None
    albumart: Optional[str] = None
    year: Union[str, int, None] = None
    icon: Optional[str] = None

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
    title: Optional[str] = None
    availableListViews: List[str]
    items: List[ListItem]


class Navigation(BaseModel):
    prev: UriItem
    lists: List[ListContainer]
    info: ListItem


class BrowseResponse(BaseModel):
    navigation: Navigation


class VolumioResponse(BaseModel):
    success: bool
    reason: Optional[str]


class ResultList(BaseModel):
    __root__: List[str]


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
    __root__: Dict[str, List[str]]


class PlayerResponse(BaseModel):
    time: int
    response: str


class MixcloudResult(BaseModel):
    key: str
    url: str
    name: str
