from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class BaseDataclass:
    @classmethod
    def read_file(cls, path: Path) -> Iterable["BaseDataclass"]:
        return cls.read_str(path.read_text(encoding="utf-8"))

    @classmethod
    def read_str(cls, content: str) -> Iterable["BaseDataclass"]:
        return cls.read_lines(content.splitlines())

    @classmethod
    def read_lines(cls, lines: list[str]) -> Iterable["BaseDataclass"]:
        if not lines:
            return []
        cls._read_lines(lines)

    @classmethod
    def _read_lines(cls, lines: list[str]) -> Iterable["BaseDataclass"]:
        raise NotImplementedError()
