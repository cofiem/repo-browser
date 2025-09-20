"""Models for repository data."""
import csv
import datetime
import enum
import logging
import pathlib
import typing
from importlib.resources import files

import attrs
from beartype import beartype

from intrigue import utils
from intrigue.gpg import models as gpg_models

logger = logging.getLogger(__name__)


@beartype
@attrs.frozen
class RepositorySourceEntry:
    """An entry in an apt list or sources file
    or just the url to an APT repository."""

    url: str
    """Where the content for an instance was obtained."""

    distributions: typing.Optional[list[str]] = None
    """The distributions for this repository sources entry."""

    components: typing.Optional[list[str]] = None
    """The components for this repository sources entry."""

    architectures: typing.Optional[list[str]] = None
    """The machine architectures for this repository sources entry."""

    signed_by: str | None = None
    """The url to the GPG public key used to verify files in this repository."""

    def with_architectures(self, values: list[str], action: str = "extend"):
        return self._new_items(values, action, "architectures")

    def with_components(self, values: list[str], action: str = "extend"):
        return self._new_items(values, action, "components")

    def with_distributions(self, values: list[str], action: str = "extend"):
        return self._new_items(values, action, "distributions")

    def with_signed_by(self, value: str | pathlib.Path | None):
        if not value:
            value = None
        elif isinstance(value, str) and value.strip() and value.startswith("http"):
            value = value.strip()
        elif isinstance(value, str) and value.strip() and not value.startswith("http"):
            value = pathlib.Path(value.strip())
        else:
            raise ValueError(f"Unknown signed by value '{value}'.")
        return self._new_item(value, "signed_by")

    #         # TODO: param_url can be a url or apt one-line list style
    #         # TODO: using find.detect_landmarks to figure out where in the repo the url is located
    #         #  TODO: allow searching apt repo, by guessing the path to the known files, parsing them, and showing matches
    #         # build base url
    #         parts = apt_utils.from_url(param_url)
    #         kwargs = {
    #             "repository": parts.netloc,
    #             "directory": parts.path,
    #         }

    def as_querystring(self):
        return {
            "url": self.url,
            "distribution": " ".join(self.distributions or []),
            "component": " ".join(self.components or []),
            "architecture": " ".join(self.architectures or []),
            "sign_url": self.signed_by or "",
        }

    def _new_items(self, values: typing.Optional[list[str]], action: str, field: str):
        existing = getattr(self, field)
        if action == "extend":
            items = [*(existing or []), *(values or [])]
        elif action == "replace":
            items = values
        else:
            raise ValueError(
                f"Unknown action '{action}'. " "Expected 'extend' or 'replace'."
            )
        items = sorted(set(i.strip() for i in items if i and i.strip()))
        if not items:
            items = []
        return attrs.evolve(self, **{field: items})

    def _new_item(self, value: str, field: str):
        if value is not None and (not value or not value.strip()):
            # Allow None, but not empty strings
            raise ValueError(f"Cannot set empty string for {field}.")
        return attrs.evolve(self, **{field: value})


@beartype
@attrs.frozen
class Field:
    """A field in a control file."""

    name: str
    values: list[str]


@beartype
@attrs.frozen
class Paragraph:
    """A paragraph in a control file."""

    fields: list[Field] = attrs.field(factory=list)

    def get_field_value(self, name: str) -> typing.Optional[Field]:
        for field in self.fields:
            if field.name == name:
                return field
        return None


@beartype
@attrs.frozen
class Control:
    """A Debian apt control file."""

    paragraphs: list[Paragraph] = attrs.field(factory=list)


@beartype
@enum.unique
class FileHashType(enum.Enum):
    """Enumeration of available hash types."""

    Unknown = 0

    Md5 = 1
    Sha1 = 2
    Sha256 = 3
    Sha512 = 4

    @classmethod
    def digest_length(cls, name) -> typing.Optional[int]:
        if not name:
            return None
        return {
            cls.Md5: 32,
            cls.Sha1: 40,
            cls.Sha256: 64,
            cls.Sha512: 128,
        }.get(name)

    @classmethod
    def from_control_field(cls, name: str):
        known = {
            "MD5Sum": cls.Md5,
            "MD5sum": cls.Md5,
            "SHA1": cls.Sha1,
            "SHA256": cls.Sha256,
            "SHA512": cls.Sha512,
        }
        if name in known:
            return known[name]
        raise ValueError(f"Unknown file hash type '{name}'.")

    def to_control_field(self, is_release_file: bool) -> str:
        known = {
            self.Md5: "MD5Sum" if is_release_file else "MD5sum",
            self.Sha1: "SHA1",
            self.Sha256: "SHA256",
            self.Sha512: "SHA512",
        }
        if self in known:
            return known[self]
        raise ValueError(f"Unknown file hash type '{self}'.")

    @classmethod
    def preferred(cls):
        """The order of preference for the file hash types.
        Most preferred is first."""
        return cls.Sha512, cls.Sha256, cls.Sha1, cls.Md5


@beartype
@attrs.frozen
class FileInfo:
    """Details about an APT file."""

    url_relative: str

    hash_type: FileHashType
    """The file hash type."""

    hash_value: str
    """The file hash value."""

    size_bytes: int
    """The file size in bytes."""


@beartype
@attrs.frozen
class Release:
    """An APT repository Release file."""

    url: str
    """Where the content for an instance was obtained."""

    origin: str
    """Optional field indicating the origin of the repository, 
    a single line of free form text."""

    label: str
    """Optional field including some kind of label, a single line of free form text."""

    suite: str
    """The Suite field may describe the suite. A suite is a single word.
    In Debian, this shall be one of oldstable, stable, testing, unstable, 
    or experimental; with optional suffixes such as -updates."""

    version: str | None
    """The Version field, if specified, shall be the version of the release. 
    This is usually a sequence of integers separated by the character . (full stop). """

    codename: str | None
    """The Codename field shall describe the codename of the release. 
    A codename is a single word."""

    changelogs: str | None
    """The Changelogs field tells the client where to find changelogs, usually a URL."""

    date: datetime.datetime
    """The Date field shall specify the time at which the Release file was created."""

    valid_until: datetime.datetime | None
    """The Valid-Until field may specify at which time the Release file 
    should be considered expired by the client. """

    no_support_for_architecture_all: str | None
    """decouple the introduction of indexes like Contents-all 
    from the introduction of Packages-all."""

    architectures: list[str]
    """Whitespace separated unique single words identifying machine architectures."""

    components: list[str]
    """A whitespace separated list of areas.
    May also include be prefixed by parts of the path following 
    the directory beneath dists, if the Release file is not 
    in a directory directly beneath dists/."""

    description: str | None = ''
    """Free-text description of the contents covered by the Release file."""

    acquire_by_hash: str | None = 'no'
    """A boolean, defaults to 'no'.
    A value of "yes" indicates that the server supports 
    the optional "by-hash" locations as an alternative 
    to the canonical location (and name) of an index file."""

    hashes: list[FileInfo] = attrs.field(factory=list)
    """Describe the package index files present.
    When release signature is available it certifies 
    that listed index files and files referenced by those index files are genuine.
    
    Clients may not use the MD5Sum and SHA1 fields for security purposes, 
    and must require a SHA256 or a SHA512 field. 
    """


@beartype
@attrs.frozen
class RepositoryRelease:
    """Possible Debian repository Release files."""

    release: Release
    """The APT repository Release file."""
    signature: gpg_models.SignaturePacket | None = None
    """The signature used to sign the Release file."""
    public_key: gpg_models.PublicKeyPacket | None = None
    """The public key used to verify the signature."""

@beartype
@attrs.frozen
class AptRepoKnownNames:
    group: str
    category: str
    value: str
    title: str

    @classmethod
    def from_resources_csv_file(cls):
        resource_name = "intrigue.resources.repos-apt.csv"
        with files(utils.get_name_under()).joinpath(resource_name).open('r', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield AptRepoKnownNames(
                    group=row.get('group', ''),
                    category=row.get('category', ''),
                    value=row.get('value', ''),
                    title=row.get('title', ''),
                )

