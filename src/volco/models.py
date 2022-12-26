import re
from typing import List, Optional, Union

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
        if self.uri is None:
            return None
        if self.uri.startswith("mixcloud"):
            return re.sub(
                r"^(mixcloud/)(.+)?(cloudcast@cloudcastId=[^@]+)(@.+)?$",
                r"\1\3",
                self.uri,
            )
        if self.uri.startswith("soundcloud"):
            return re.sub(
                r"^(soundcloud/)(.+)?(track@trackId=[^@]+)(@.+)?$", r"\1\3", self.uri
            )
        return self.uri


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
