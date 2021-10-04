from datetime import datetime
from pathlib import Path
from typing import Optional, Iterable
from urllib.parse import urljoin

from hill.data.apt.item.control import Control
from hill.data.apt.item.file_hash import FileHash
from hill.data.apt.item.package_relation import PackageRelation
from hill.data.apt.item.package_tag import PackageTag
from hill.data.apt.item.paragraph import Paragraph
from hill.data.common.archive import Archive


class Controls:
    def __init__(self):
        self._archive = Archive()

    def translation_name_urls(self, base_url: str, dist: str, comp: str, language: str):
        """
        $ARCHIVE_ROOT/dists/$DIST/$COMP/i18n/Translation-$LANG(.ext)

        $LANG is <lang>_[<country>].
        """
        path = Path("dists", dist, comp, "i18n", f"Translation-{language}")
        return self._name_urls(base_url, path)

    def translation_hash_url(
        self, base_url: str, dist: str, comp: str, hash_type: str, hash_value: str
    ):
        """$ARCHIVE_ROOT/dists/$DIST/$COMP/i18n/by-hash/$HASHTYPE/$HASHVALUE"""
        path = Path("dists", dist, comp, "i18n", "by-hash", hash_type, hash_value)
        return urljoin(base_url, str(path))

    def contents_name_urls(
        self, base_url: str, dist: str, comp: Optional[str], arch: str
    ):
        """
        - $ARCHIVE_ROOT/dists/$DIST/Contents-$SARCH(.ext)
        - $ARCHIVE_ROOT/dists/$DIST/$COMP/Contents-$SARCH(.ext)

        $SARCH is either a binary architecture or the pseudo-architecture "source".
        """
        if comp:
            path = Path("dists", dist, comp, f"Contents-{arch}")
        else:
            path = Path("dists", dist, f"Contents-{arch}")
        return self._name_urls(base_url, path)

    def contents_hash_url(
        self,
        base_url: str,
        dist: str,
        comp: Optional[str],
        hash_type: str,
        hash_value: str,
    ):
        """
        - $ARCHIVE_ROOT/dists/$DIST/by-hash/$HASHTYPE/$HASHVALUE
        - $ARCHIVE_ROOT/dists/$DIST/$COMP/by-hash/$HASHTYPE/$HASHVALUE
        """
        if comp:
            path = Path("dists", dist, comp, "by-hash", hash_type, hash_value)
        else:
            path = Path("dists", dist, "by-hash", hash_type, hash_value)
        return self._name_urls(base_url, path)

    def package_name_urls(self, base_url: str, dist: str, comp: str, arch: str):
        """$ARCHIVE_ROOT/dists/$DIST/$COMP/binary-$ARCH/Package(.ext)"""
        path = Path("dists", dist, comp, f"binary-{arch}", "Package")
        return self._name_urls(base_url, path)

    def package_hash_url(
        self,
        base_url: str,
        dist: str,
        comp: str,
        arch: str,
        hash_type: str,
        hash_value: str,
    ):
        """$ARCHIVE_ROOT/dists/$DIST/$COMP/binary-$ARCH/by-hash/$HASHTYPE/$HASHVALUE"""
        path = Path(
            "dists", dist, comp, f"binary-{arch}", "by-hash", hash_type, hash_value
        )
        return self._name_urls(base_url, path)

    def release_combined_url(self, base_url: str, dist: str):
        """$ARCHIVE_ROOT/dists/$DISTRIBUTION/InRelease"""
        path = Path("dists", dist, "InRelease")
        return urljoin(base_url, str(path))

    def release_clear_url(self, base_url: str, dist: str):
        """$ARCHIVE_ROOT/dists/$DISTRIBUTION/Release"""
        path = Path("dists", dist, "Release")
        return urljoin(base_url, str(path))

    def release_detached_url(self, base_url: str, dist: str):
        """$ARCHIVE_ROOT/dists/$DISTRIBUTION/Release.gpg"""
        path = Path("dists", dist, "Release.gpg")
        return urljoin(base_url, str(path))

    def available_priorities(self):
        return ["required", "important", "standard", "optional", "extra"]

    def read_file(self, path: Path) -> Control:
        results = []
        for entry in self._archive.from_path(path):
            content = self._archive.from_entry(path, entry)
            item = self.read_content(content)
            results.append(item)

        if len(results) != 1:
            raise ValueError("'Unexpected number of control files from '{path}'.'")

        return results[0]

    def read_content(self, content: str) -> Control:
        return self.read_lines(content.splitlines())

    def read_lines(self, lines: Iterable[str]) -> Control:
        control = Control()
        if not lines:
            return control

        current_para = None
        current_key = None
        current_value = None
        for line in lines:
            if current_para is None:
                current_para = Paragraph()

            # paragraph end (blank line)
            if (not line or not line.strip()) and current_para:
                if current_key:
                    self.update_para(current_para, current_key, current_value)
                control.paragraphs.append(current_para)
                current_para = Paragraph()
                continue

            # comment line
            if line.startswith("#"):
                continue

            # continuation line
            if line != line.lstrip():
                current_value.append(line)
                continue

            # add previous key and value to file
            if current_key:
                self.update_para(current_para, current_key, current_value)
            current_key, current_value = line.split(":", maxsplit=1)
            current_value = [current_value]

        if current_para and current_key:
            self.update_para(current_para, current_key, current_value)

        if current_para is not None:
            control.paragraphs.append(current_para)

        return control

    def update_para(self, para: "Paragraph", key: str, value: Iterable[str]) -> None:

        ignored_keys = [
            "Standards-Version",
            "Testsuite",
            "Rules-Requires-Root",
            "Packages-Require-Authorization",
            "Phased-Update-Percentage",
            "Multi-Arch",
            "Ruby-Versions",
            "Python-Egg-Name",
            "Go-Import-Path",
            "Lua-Versions",
            "Cnf-Ignore-Commands",
        ]

        if key == "Origin":
            para.origin = self._get_single_value(value)
        elif key == "Label":
            para.label = self._get_single_value(value)
        elif key == "Version":
            para.version = self._get_single_value(value)
        elif key == "Codename":
            para.codename = self._get_single_value(value)
        elif key == "Date":
            para.created_date = self._get_date(self._get_single_value(value))
        elif key == "Suite":
            para.suite = self._get_single_value(value)
        elif key == "Acquire-By-Hash":
            para.acquire_by_hash = self._get_bool(self._get_single_value(value))
        elif key in ["Architecture", "Architectures"]:
            para.architectures.extend(self._get_whitespace_items(value))
        elif key == "Components":
            para.components.extend(self._get_whitespace_items(value))
        elif key == "Description":
            para.description = self._get_single_value(value)
        elif key == "Description-md5":
            para.description_md5 = self._get_single_value(value)
        elif key in ["MD5Sum", "MD5sum"]:
            sums_type, sums_value = self._get_sums_decide(value)
            if sums_type == "item_hash":
                para.hash_md5 = sums_value
            elif sums_type == "hash_files":
                para.hash_files_md5.extend(sums_value)
            else:
                raise ValueError()
        elif key == "SHA256":
            sums_type, sums_value = self._get_sums_decide(value)
            if sums_type == "item_hash":
                para.hash_sha256 = sums_value
            elif sums_type == "hash_files":
                para.hash_files_sha256.extend(sums_value)
            else:
                raise ValueError()
        elif key == "SHA512":
            sums_type, sums_value = self._get_sums_decide(value)
            if sums_type == "item_hash":
                para.hash_sha512 = sums_value
            elif sums_type == "hash_files":
                para.hash_files_sha512.extend(sums_value)
            else:
                raise ValueError()
        elif key == "Package":
            para.package = self._get_single_value(value)
        elif key == "Source":
            para.source = self._get_single_value(value)
        elif key == "Homepage":
            para.homepage_url = self._get_single_value(value)
        elif key == "Section":
            para.section = self._get_single_value(value)
        elif key == "Priority":
            para.priority = self._get_single_value(value)
        elif key == "Installed-Size":
            para.installed_size = self._get_int(self._get_single_value(value))
        elif key == "Size":
            para.compressed_size = self._get_int(self._get_single_value(value))
        elif key == "Filename":
            para.filename = self._get_single_value(value)
        elif key == "Tag":
            para.tags.extend(PackageTag.from_lines(value))
        elif key == "Maintainer":
            para.maintainers.extend(self._get_contact(value))
        elif key == "Uploaders":
            para.uploaders.extend(self._get_contact(value))
        elif key == "Depends":
            para.depends.extend(PackageRelation.from_lines(value))
        elif key == "Pre-Depends":
            para.pre_depends.extend(PackageRelation.from_lines(value))
        elif key == "Recommends":
            para.recommends.extend(PackageRelation.from_lines(value))
        elif key == "Suggests":
            para.suggests.extend(PackageRelation.from_lines(value))
        elif key == "Breaks":
            para.breaks.extend(PackageRelation.from_lines(value))
        elif key == "Conflicts":
            para.conflicts.extend(PackageRelation.from_lines(value))
        elif key == "Provides":
            para.provides.extend(PackageRelation.from_lines(value))
        elif key == "Replaces":
            para.replaces.extend(PackageRelation.from_lines(value))
        elif key == "Enhances":
            para.enhances.extend(PackageRelation.from_lines(value))
        elif key == "Built-Using":
            para.built_using.extend(PackageRelation.from_lines(value))
        elif key == "Build-Depends":
            para.build_depends.extend(PackageRelation.from_lines(value))
        elif key == "Build-Essential":
            para.build_essential = self._get_bool(self._get_single_value(value))
        elif key == "Essential":
            para.essential = self._get_bool(self._get_single_value(value))
        elif key in ignored_keys:
            pass
        else:
            para.ignored_fields.append((key, value))

    def _get_single_value(self, value: Iterable[str]):
        if not value:
            return None
        return " ".join([i.strip() for i in value if i is not None])

    def _get_date(self, value: str):
        formats = [
            "%a, %d %b %Y %H:%M:%S %Z",
            "%a, %d %b %Y %H:%M:%S %z",
        ]
        for item in formats:
            try:
                return datetime.strptime(value, item)
            except ValueError:
                pass
        return None

    def _get_bool(self, value: str):
        if not value:
            return False
        value = str(value).strip().lower()
        return value in ["true", "1", "yes", "y", "t"]

    def _get_int(self, value: str):
        if not value:
            return 0
        value = str(value).strip()
        return int(value, 10)

    def _get_whitespace_items(self, value: Iterable[str]):
        for item in value:
            for entry in item.split():
                yield entry

    def _get_contact(self, value: Iterable[str]):
        for item in value:
            for entry in item.split(","):
                name, email = entry.split("<", maxsplit=1)
                yield name.strip(), email.strip(" <>")

    def _get_sums(self, value: Iterable[str]):
        for item in value:
            if not item or not item.strip():
                continue
            values = item.lstrip().split()
            if len(values) == 1:
                yield values[0]
            elif len(values) == 3:
                item_hash, item_size, item_url = values
                yield FileHash(
                    hash_value=item_hash.strip(),
                    size_bytes=int(item_size.strip(), 10),
                    name=item_url,
                )
            else:
                raise ValueError()

    def _get_sums_decide(self, value: Iterable[str]):
        items = list(self._get_sums(value))
        if len(items) == 1 and isinstance(items[0], str):
            return "item_hash", self._get_single_value(items)
        elif len(items) > 0 and isinstance(items[0], FileHash):
            return "hash_files", items
        else:
            raise ValueError()

    def _name_urls(self, base_url: str, path: Path):
        urls = []
        for suffix in self._archive.compression_suffixes:
            url_path = str(path.with_suffix(suffix) if suffix else path)
            url = urljoin(base_url, url_path)
            urls.append(url)
        return urls
