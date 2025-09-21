"""Models for repository data."""

import csv
import logging
from importlib.resources import files

import attrs
from beartype import beartype

logger = logging.getLogger(__name__)


@beartype
@attrs.frozen
class AptRepoKnownNames:
    text: str
    url: str
    sign_url: str
    distribution: str
    component: str
    architecture: str
    notes: str

    @classmethod
    def from_resources_csv_file(cls):
        with (
            files("intrigue.resources")
            .joinpath("repos-apt.csv")
            .open("r", encoding="utf-8") as f
        ):
            reader = csv.DictReader(f)
            for row in reader:
                yield AptRepoKnownNames(
                    text=row.get("text") or "",
                    url=row.get("url") or "",
                    sign_url=row.get("sign_url") or "",
                    distribution=row.get("distribution") or "",
                    component=row.get("component") or "",
                    architecture=row.get("architecture") or "",
                    notes=row.get("notes") or "",
                )


@beartype
@attrs.frozen
class KnownNames:
    group: str
    category: str
    value: str
    date: str
    title: str

    @classmethod
    def from_resources_csv_file(cls):
        with (
            files("intrigue.resources")
            .joinpath("known.csv")
            .open("r", encoding="utf-8") as f
        ):
            reader = csv.DictReader(f, dialect="excel")
            for row in reader:
                yield KnownNames(
                    group=row.get("group") or "",
                    category=row.get("category") or "",
                    value=row.get("value") or "",
                    date=row.get("date") or "",
                    title=row.get("title") or "",
                )
