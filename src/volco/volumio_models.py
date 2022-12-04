import re

from pydantic import BaseModel


class UriItem(BaseModel):
    uri: str


class ListItem(BaseModel):
    service: str
    type: str
    title: str
    uri: str
    album: str = None
    artist: str = None
    duration: int = None
    albumart: str = None
    year: str | int = None
    icon: str = None

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
    title: str = None
    availableListViews: list[str]
    items: list[ListItem]


class Navigation(BaseModel):
    prev: UriItem
    lists: list[ListContainer]
    info: ListItem


class BrowseResponse(BaseModel):
    navigation: Navigation


class TrackSpec(BaseModel):
    service: str
    uri: str

    def __hash__(self):
        return hash(self.service + self.uri)


class VolumioResponse(BaseModel):
    success: bool
    reason: str | None


class ResultList(BaseModel):
    __root__: list[str]


class ToastMessage(BaseModel):
    message: str
    title: str
    type: str
