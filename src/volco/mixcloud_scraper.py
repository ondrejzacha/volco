from functools import lru_cache
import requests

import itertools
import time

import pandas as pd

from .volumio_controller import TrackSpec

from .constants import HEADERS
from typing import Dict, Tuple
from urllib.parse import quote_plus, urlparse

import requests

MIXCLOUD_URL = "https://www.mixcloud.com/graphql"


COLS_OF_INTEREST = [
    "key",
    "url",
    "name",
    "created_time",
    "created_time",
    "play_count",
    "favorite_count",
    "audio_length",
    "show_name",
    "show_date",
    "base_show",
    "guest",
]


def first_created_time(records):
    return min(record["created_time"] for record in records)


def pull_latest_shows(
    user: str = "NTSRadio",
    min_date: str = "2022-01-01",  # FIXME
    header_generator: "Optional[Iterable[dict]]" = None,
) -> "List[List[Dict[str, Any]]]":
    header_generator = header_generator or itertools.cycle(HEADERS)

    all_records: "List[List[Dict[str, Any]]]" = []

    records = None
    starting_url = f"https://api.mixcloud.com/{user}/cloudcasts/"
    url = starting_url

    while records is None or first_created_time(records) > min_date:
        r = requests.get(url, headers=next(header_generator))
        data = r.json()
        records = data["data"]
        all_records.append(records)
        url = data["paging"]["next"]
        print(f"Next url: {url}")
        time.sleep(0.1)

    return all_records


def _to_df(records):
    records_df = pd.DataFrame([*itertools.chain(*records)])
    records_df = records_df.drop_duplicates(subset=["key"]).reset_index(drop=True)
    return records_df


def preprocess_records(records: "Collection[dict]") -> pd.DataFrame:
    records_df = _to_df(records)
    records_df[["show_name", "show_date"]] = records_df.name.str.rsplit(
        " - ", n=1, expand=True
    )
    records_df[["base_show", "guest"]] = records_df["show_name"].str.split(
        " w/ ", n=1, expand=True
    )
    records_df = records_df[COLS_OF_INTEREST]
    return records_df


def main(
    user: str = "NTSRadio", min_date: str = "2022-01-01",  # FIXME
):
    records = pull_latest_shows(user=user, min_date=min_date)
    df = preprocess_records(records)
    # df.to_sql()


########


@lru_cache
def get_track_spec(key: str) -> TrackSpec:
    payload = Mixcloud(key).get_volumio_payload()
    return TrackSpec.parse_obj(payload)


class Mixcloud:
    def __init__(self, url: str) -> None:
        self.url = url

    def get_volumio_payload(self) -> Dict[str, str]:
        track_id = self.get_track_id()
        encoded_track_id = quote_plus(track_id)
        payload = {
            "uri": f"mixcloud/featured/cloudcast@cloudcastId"
            f"={encoded_track_id}@showMoreFromUser=1",
            "service": "mixcloud",
        }
        return payload

    def get_track_id(self) -> str:
        username, slug = self._get_path_elements()
        payload = {
            "query": "query cloudcastQuery($lookup: CloudcastLookup!) "
            "{cloudcast: cloudcastLookup(lookup: $lookup) {id name slug}}",
            "variables": {"lookup": {"username": username, "slug": slug,}},
        }
        res = requests.post(
            MIXCLOUD_URL,
            json=payload,
            headers={"content-type": "application/json", "accept": "application/json",},
        )
        if res.status_code != 200:
            raise RuntimeError(f"Got status: {res.status_code}")
        print(res.json())
        # FIXME
        cloudcast = res.json().get("data", {}).get("cloudcast")
        if cloudcast is not None:
            return cloudcast.get("id")

        return None

    def _get_path_elements(self) -> Tuple[str, str]:
        parsed = urlparse(self.url)
        path_elements = [
            element for element in parsed.path.split("/") if len(element) > 0
        ]
        if len(path_elements) != 2:
            raise ValueError("Invalid URL")
        username, slug = path_elements
        return username, slug
