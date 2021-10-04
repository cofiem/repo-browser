from dataclasses import dataclass
from typing import Optional, Iterable


@dataclass
class PackageTag:

    section: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None

    def __str__(self):
        s = self.section
        c = self.category
        sc = self.sub_category
        if s and c and sc:
            return f"{s}::{c}:{sc}"
        elif s and c and not sc:
            return f"{s}::{c}"
        elif not s and c and sc:
            return f"{c}:{sc}"
        elif s and not c and not sc:
            return s
        else:
            raise ValueError(self)

    @classmethod
    def display(cls, value: list["PackageTag"]):
        return ", ".join([str(i) for i in value])

    @classmethod
    def from_lines(cls, value: Iterable[str]) -> Iterable["PackageTag"]:
        for item in value:
            for entry in item.split(","):
                entry = entry.strip()

                # section
                if "::" in entry:
                    section, entry = entry.split("::")
                elif ":" not in entry:
                    section = entry
                    entry = ""
                else:
                    section = None

                # category
                if ":" in entry:
                    category, entry = entry.split(":")
                elif section:
                    category = entry
                    entry = None
                else:
                    category = None

                # section
                sub_category = entry

                if section or category or sub_category:
                    yield PackageTag(
                        section=section, category=category, sub_category=sub_category
                    )
