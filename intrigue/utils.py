"""Utilities for data."""

import io
import pathlib
import typing
from datetime import datetime
from importlib.metadata import PackageNotFoundError, distribution
from importlib.resources import as_file, files

import attrs
import cattrs
import zoneinfo
from beartype import beartype

from intrigue.apt.utils import AptException


@beartype
def get_name_dash() -> str:
    """Get the package name with word separated by dashes."""
    return "repo-browser"


@beartype
def get_name_under() -> str:
    """Get the package name with word separated by underscores."""
    return "repo_browser"


@beartype
def get_version() -> typing.Optional[str]:
    """Get the package version."""
    try:
        dist = distribution(get_name_dash())
    except PackageNotFoundError:
        pass

    else:
        return dist.version

    try:
        with as_file(files(get_name_under()).joinpath("cli.py")) as file_path:
            return (file_path.parent.parent.parent / "VERSION").read_text().strip()
    except FileNotFoundError:
        pass

    return None


@beartype
def load_data_item(data_class, data: typing.Mapping[str, typing.Any]):
    """Populate data classes from a data map."""
    available_fields = attrs.fields_dict(data_class)
    prog_key = get_name_under()
    mapping_fields = {
        value.metadata.get(prog_key, {}).get("key"): key
        for key, value in available_fields.items()
        if value.metadata.get(prog_key, {}).get("key")
    }
    result_raw = {}
    for key, value in data.items():
        field_name = mapping_fields.get(key)
        if not field_name:
            raise AptException(f"Missing field {key}={value}.")
        result_raw[field_name] = value
    result = cattrs.structure(result_raw, data_class)
    return result


@beartype
def get_date(value: str):
    if not value or not value.strip():
        return None
    date_formats = [
        "%a, %d %b %Y %H:%M:%S",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S %z",
    ]
    for date_format in date_formats:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            pass

        try:
            date_raw, offset_raw = value.rsplit(" ", maxsplit=1)
            date_naive = datetime.strptime(date_raw, date_format)
            tz_info = zoneinfo.ZoneInfo(offset_raw)
            date_aware = date_naive.replace(tzinfo=tz_info)
            return date_aware
        except ValueError:
            pass
        except zoneinfo.ZoneInfoNotFoundError:
            pass
    raise AptException(f"Cannot parse date {value}.")


ARCHIVE_EXTENSIONS = {
    "xz": [".xz", ".lzma"],
    "gz": [".gz", ".gzip"],
    "bz2": [".bz2", ".bzip2"],
    "tar": [".tar"],
    "zip": [".zip"],
}


@beartype
def archive_extensions(name: str):
    for group, items in ARCHIVE_EXTENSIONS.items():
        for item in items:
            yield f"{name}{item}"


@beartype
def read_archive(
    name: str, content: bytes
) -> typing.Generator[tuple[str, bytes], typing.Any, None]:
    """Read the content with the given name and generate the raw content it contains."""

    path_name = pathlib.Path(name)
    suffixes = path_name.suffixes

    if set(suffixes).intersection(ARCHIVE_EXTENSIONS["tar"]):
        import tarfile

        with io.BytesIO(content) as bio, tarfile.open(name, "r|*", bio) as container:
            for element in container:
                file_content = container.extractfile(element)
                if file_content is not None:
                    yield element.name, file_content.read()

    if set(suffixes).intersection(ARCHIVE_EXTENSIONS["zip"]):
        import zipfile

        with io.BytesIO(content) as bio, zipfile.ZipFile(bio, "r") as container:
            for element in container.infolist():
                if element.is_dir():
                    continue
                with container.open(element, "r") as file_content:
                    if file_content is not None:
                        yield element.filename, file_content.read()

    if set(suffixes).intersection(ARCHIVE_EXTENSIONS["xz"]):
        import lzma

        yield name, lzma.decompress(content)

    if set(suffixes).intersection(ARCHIVE_EXTENSIONS["gz"]):
        import gzip

        yield name, gzip.decompress(content)

    if set(suffixes).intersection(ARCHIVE_EXTENSIONS["bz2"]):
        import bz2

        yield name, bz2.decompress(content)

    yield name, content
