import re
from dataclasses import dataclass, field
from typing import Optional, Iterable, Union


@dataclass
class PackageRelation:

    name: Optional[str] = None

    restriction_type: Optional[str] = None  # ([<<, <=, =, >=, >>] [ver])
    restriction_version: Optional[str] = None

    allowed_architectures: Optional[list[str]] = field(default_factory=list)
    ignored_architectures: Optional[list[str]] = field(default_factory=list)

    def __str__(self):
        if self.restriction_type and self.restriction_version:
            ver = f"({self.restriction_type} {self.restriction_version})"
        else:
            ver = None

        allowed = " ".join(self.allowed_architectures)
        ignored = " ".join([f"!{i}" for i in self.ignored_architectures])
        if ignored or allowed:
            arches = f"[{ignored + allowed}]"
        else:
            arches = None

        me = " ".join((i for i in [self.name, ver, arches] if i)).strip()
        return me

    @classmethod
    def display(cls, value: list[Union["PackageRelation", list["PackageRelation"]]]):
        rel = []
        for item in value:
            if isinstance(item, PackageRelation):
                rel.append(str(item))
            else:
                rel.append(" | ".join([str(i) for i in item]))
        return ", ".join(rel)

    @classmethod
    def from_lines(
        cls, value: Iterable[str]
    ) -> list[Union["PackageRelation", list["PackageRelation"]]]:
        pattern = re.compile(
            r"^(?P<name>\S+)\s*(\((?P<rel>[<=>]+)\s*(?P<ver>.*)\))?\s*(\[(?P<arch>.*)\])?$"
        )
        results = []  # type: list[Union["PackageRelation", list["PackageRelation"]]]
        for item in value:
            for entry in item.split(","):
                alts = []  # type: list["PackageRelation"]
                for alt in entry.split("|"):
                    match = pattern.match(alt.strip())
                    name = match.group("name")
                    restriction_type = match.group("rel")
                    restriction_version = match.group("ver")

                    allowed = []
                    ignored = []
                    arches = (match.group("arch") or "").split(" ")
                    for arch in arches:
                        arch = arch.strip()
                        if not arch:
                            continue
                        if arch.startswith("!"):
                            ignored.append(arch[1:])
                        else:
                            allowed.append(arch)
                    rel = PackageRelation(
                        name=name,
                        restriction_type=restriction_type,
                        restriction_version=restriction_version,
                        allowed_architectures=allowed,
                        ignored_architectures=ignored,
                    )
                    alts.append(rel)

                if len(alts) == 1:
                    results.extend(alts)
                elif len(alts) > 1:
                    results.append(alts)

        check = cls.display(results)
        return results
