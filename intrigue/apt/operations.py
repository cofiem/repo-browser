import logging
import typing

from intrigue.apt import models as apt_models
from intrigue import utils

logger = logging.getLogger(__name__)


def paragraph(content: str) -> apt_models.Paragraph:
    """Parse string content into a Paragraph item."""
    lines = (content or "").strip().splitlines()
    if not lines:
        return apt_models.Paragraph()

    fields = []

    current_key: typing.Optional[str] = None
    current_value: typing.Optional[list[str]] = None
    for line in lines:
        # paragraph end (blank line)
        if (not line or not line.strip()) and fields:
            raise ValueError("A paragraph cannot contain an empty line.")

        # comment line
        if line.startswith("#"):
            continue

        # continuation line
        if line != line.lstrip():
            current_value.append(line.lstrip())
            continue

        # add previous key and value to file
        if current_key:
            fields.append(apt_models.Field(name=current_key, values=current_value))

        # get the key and value
        if ":" not in line:
            raise ValueError(f"Invalid paragraph line '{line}'.")

        line_key, line_value = line.split(":", maxsplit=1)
        current_key = line_key.strip()
        current_value = [line_value.strip()]

    if current_key:
        fields.append(apt_models.Field(name=current_key, values=current_value))

    return apt_models.Paragraph(fields=fields)


def control(content: str) -> apt_models.Control:
    """Parse string content into a Control item."""
    lines = (content or "").strip().splitlines()
    if not lines:
        return apt_models.Control()

    paragraphs = []

    current_lines = []
    for line in lines:
        # paragraph end (blank line)
        if (not line or not line.strip()) and current_lines:
            para = paragraph("\n".join(current_lines))
            paragraphs.append(para)
            current_lines = []
            continue

        current_lines.append(line)

    if current_lines:
        para = paragraph("\n".join(current_lines))
        paragraphs.append(para)

    return apt_models.Control(paragraphs=paragraphs)


def release(content: str) -> apt_models.Release | None:
    """Parse string content into a Release item."""
    control_item = control(content)

    if not control or len(control_item.paragraphs) != 1:
        logger.warning("Unexpected release format.")
        return None

    def _get(name: str, process: str = "one"):
        f = p.get_field_value(name)
        if not f:
            return None

        if process == "one":
            if len(f.values) != 1:
                raise ValueError("Unexpected field values '%s'.", f.values)
            return f.values[0]
        elif process == "space_sep_items":
            return [i for v in f.values for i in v.split(" ")]
        elif process == "file_info":
            result = []
            for v in f.values:
                if not v or not v.strip():
                    continue
                hash_type = apt_models.FileHashType.from_control_field(name)
                hash_value, size_bytes, rel_url = [i for i in v.split(" ") if i]
                result.append(
                    apt_models.FileInfo(
                        url_relative=rel_url,
                        hash_type=hash_type,
                        hash_value=hash_value,
                        size_bytes=int(size_bytes),
                    )
                )
            return result
        else:
            raise ValueError(f"Unknown process {process}")

    p = control_item.paragraphs[0]
    data = {
        "acquire_by_hash": _get("Acquire-By-Hash"),
        "architectures": _get("Architectures", "space_sep_items"),
        "codename": _get("Codename"),
        "components": _get("Components", "space_sep_items"),
        "date": utils.get_date(_get("Date")),
        "description": _get("Description"),
        "hashes": [
            *_get("MD5Sum", "file_info"),
            *_get("SHA1", "file_info"),
            *_get("SHA256", "file_info"),
        ],
        "label": _get("Label"),
        "origin": _get("Origin"),
        "suite": _get("Suite"),
        "version": _get("Version"),
        "url": None,
        "changelogs": None,
        "no_support_for_architecture_all": None,
        "valid_until": None,
    }

    return apt_models.Release(**data)
