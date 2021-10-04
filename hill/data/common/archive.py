from bz2 import BZ2File
from gzip import GzipFile
from lzma import LZMAFile
from tarfile import TarFile
from zipfile import ZipFile
from pathlib import Path


class Archive:
    def from_path(self, path: Path):
        """Access the contents of a file archive."""
        suffix = path.suffix
        if suffix in [".xz", ".lzma"]:
            with LZMAFile(path, "r") as f:
                yield f.read()
        elif suffix in [".gz", ".gzip"]:
            with GzipFile(path, "r") as f:
                yield f.read()
        elif suffix in [".bz2", ".bzip2"]:
            with BZ2File(path, "r") as f:
                yield f.read()
        elif suffix in [".zip"]:
            with ZipFile(path, "r") as f:
                raise NotImplementedError()
        elif suffix in [".tar"]:
            with TarFile(path, "r") as f:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

    def from_stream(self, stream):
        """Access the contents of a stream archive."""
        raise NotImplementedError()

    def from_entry(self, path: Path, entry):
        """"""
        suffix = path.suffix
        if suffix in [".xz", ".lzma"]:
            return entry.decode(encoding="utf-8")
        elif suffix in [".gz", ".gzip"]:
            return entry.decode(encoding="utf-8")
        elif suffix in [".bz2", ".bzip2"]:
            return entry.decode(encoding="utf-8")
        elif suffix in [".zip"]:
            raise NotImplementedError()
        elif suffix in [".tar"]:
            raise NotImplementedError()
        else:
            raise NotImplementedError()

    @property
    def compression_suffixes(self):
        # in order of preference
        # .xz, .bz2, .gz, .lzma, (none)
        return [
            ".xz",
            ".bz2",
            ".bzip2",
            ".gz",
            ".gzip",
            ".lzma",
            None,
        ]

    @property
    def archive_suffixes(self):
        # in order of preference
        # .xz, .bz2, .gz, .lzma, (none)
        return [
            ".tar.xz",
            ".tar.bz2",
            ".tar.bzip2",
            ".tar.gz",
            ".tar.gzip",
            ".tar.lzma",
            ".zip",
            ".tar",
            None,
        ]
