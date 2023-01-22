import re
from typing import List, Optional, Union, Any
import datetime

from pydantic import BaseModel


class UriItem(BaseModel):
    uri: str


class ListItem(BaseModel):
    service: str
    type: str
    title: str
    uri: str
    album: Optional[str] = None
    artist: Optional[str] = None
    duration: Optional[int] = None
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


class State(BaseModel):
    status: str
    position: int
    title: str
    artist: str
    album: str
    albumart: str
    uri: str
    trackType: str
    seek: int
    duration: int
    samplerate: str
    channels: int
    bitrate: Any
    random: Any
    repeat: Any
    repeatSingle: bool
    consume: bool
    volume: int
    dbVolume: Any
    mute: bool
    disableVolumeControl: bool
    stream: bool
    updatedb: bool
    volatile: bool
    service: str


class StateLog(BaseModel):
    ts: datetime.datetime
    state: State
