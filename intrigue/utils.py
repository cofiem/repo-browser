"""Utilities for data."""

from __future__ import annotations

import io
import pathlib
from datetime import datetime
import typing
import zoneinfo
from importlib.metadata import PackageNotFoundError, distribution
from importlib.resources import as_file, files

import attrs
import cattrs
from django.template.defaultfilters import yesno


def get_name_dash() -> str:
    """Get the package name with word separated by dashes."""
    return "repo-browser"


def get_name_under() -> str:
    """Get the package name with word separated by underscores."""
    return "repo_browser"


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


def load_data_item(data_class, data: typing.Mapping[str, typing.Any]):
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
            raise ValueError(f"Missing field {key}={value}.")
        result_raw[field_name] = value
    result = cattrs.structure(result_raw, data_class)
    return result


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
    raise ValueError(f"Cannot parse date {value}.")


def read(name: str, content: bytes) -> typing.Generator[tuple[str, bytes], typing.Any, None]:
    """Read the content with the given name and generate the raw content it contains."""
    exts_xz = [".xz", ".lzma"]
    exts_gz = [".gz", ".gzip"]
    exts_bz2 = [".bz2", ".bzip2"]
    ext_tar = ".tar"
    ext_zip = ".zip"

    path_name = pathlib.Path(name)

    if ext_tar in path_name.suffixes:
        import tarfile

        with io.BytesIO(content) as bio, tarfile.open(name, "r|*", bio) as container:
            for element in container:
                file_content = container.extractfile(element)
                if file_content is not None:
                    yield element.name, file_content.read()

    if ext_zip in path_name.suffixes:
        import zipfile

        with io.BytesIO(content) as bio, zipfile.ZipFile(bio, "r") as container:
            for element in container.infolist():
                if element.is_dir():
                    continue
                with container.open(element, 'r') as file_content:
                    if file_content is not None:
                        yield element.filename, file_content.read()

    if any([name.endswith(ext) for ext in exts_xz]):
        import lzma
        yield name, lzma.decompress(content)

    if any([name.endswith(ext) for ext in exts_gz]):
        import gzip
        yield name, gzip.decompress(content)

    if any([name.endswith(ext) for ext in exts_bz2]):
        import bz2
        yield name, bz2.decompress(content)

    yield name, content
