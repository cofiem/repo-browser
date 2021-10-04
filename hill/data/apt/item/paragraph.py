from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from typing import Optional

from hill.data.apt.item.file_hash import FileHash
from hill.data.apt.item.file_location import FileLocation
from hill.data.apt.item.package_relation import PackageRelation
from hill.data.apt.item.package_tag import PackageTag


@dataclass
class Paragraph:
    """
    A paragraph from a Debian control file.

    Ref: https://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-package
    """

    # general
    package: Optional[str] = None
    version: Optional[str] = None
    section: Optional[str] = None
    priority: Optional[str] = None
    source: Optional[str] = None
    essential: Optional[bool] = None
    installed_size: Optional[int] = None
    compressed_size: Optional[int] = None
    homepage_url: Optional[str] = None
    package_type: Optional[str] = None
    origin: Optional[str] = None
    label: Optional[str] = None
    suite: Optional[str] = None
    codename: Optional[str] = None
    created_date: Optional[datetime] = None
    valid_until_date: Optional[datetime] = None
    not_automatic: Optional[bool] = None
    but_automatic_upgrades: Optional[bool] = None
    acquire_by_hash: Optional[bool] = None
    architectures: Optional[list[str]] = field(default_factory=list)
    components: Optional[list[str]] = field(default_factory=list)
    description: Optional[str] = None
    files_locations: Optional[list[FileLocation]] = field(default_factory=list)
    signed_by_gpg_fingerprints: Optional[list[str]] = field(default_factory=list)
    filename: Optional[str] = None
    tags: Optional[list[PackageTag]] = field(default_factory=list)
    build_essential: Optional[bool] = None

    # contact info
    maintainers: Optional[list[tuple[str, str]]] = field(default_factory=list)
    uploaders: Optional[list[tuple[str, str]]] = field(default_factory=list)

    # hashes
    hash_md5: Optional[str] = None
    description_md5: Optional[str] = None
    hash_files_md5: Optional[list[FileHash]] = field(default_factory=list)
    hash_checksums_md5: Optional[list[FileHash]] = field(default_factory=list)
    hash_sha1: Optional[str] = None
    hash_files_sha1: Optional[list[FileHash]] = field(default_factory=list)
    hash_checksums_sha1: Optional[list[FileHash]] = field(default_factory=list)
    hash_sha256: Optional[str] = None
    hash_files_sha256: Optional[list[FileHash]] = field(default_factory=list)
    hash_checksums_sha256: Optional[list[FileHash]] = field(default_factory=list)
    hash_sha512: Optional[str] = None
    hash_files_sha512: Optional[list[FileHash]] = field(default_factory=list)
    hash_checksums_sha512: Optional[list[FileHash]] = field(default_factory=list)

    # package relations
    depends: Optional[list[PackageRelation]] = field(default_factory=list)
    pre_depends: Optional[list[PackageRelation]] = field(default_factory=list)
    recommends: Optional[list[PackageRelation]] = field(default_factory=list)
    suggests: Optional[list[PackageRelation]] = field(default_factory=list)
    breaks: Optional[list[PackageRelation]] = field(default_factory=list)
    conflicts: Optional[list[PackageRelation]] = field(default_factory=list)
    provides: Optional[list[PackageRelation]] = field(default_factory=list)
    replaces: Optional[list[PackageRelation]] = field(default_factory=list)
    enhances: Optional[list[PackageRelation]] = field(default_factory=list)
    built_using: Optional[list[PackageRelation]] = field(default_factory=list)
    build_depends: Optional[list[PackageRelation]] = field(default_factory=list)

    # ignored
    ignored_fields: Optional[list[tuple[str, Any]]] = field(default_factory=list)

    def __str__(self):
        result = [
            self.origin,
            self.suite,
            self.codename,
            self.label,
            self.section,
            self.priority,
            self.package or self.source,
            self.version,
        ]
        return ", ".join([i for i in result if i])
