from dataclasses import field, dataclass
from typing import Optional


@dataclass
class FileLocationPackage:
    name: str
    section: Optional[str] = None
    area: Optional[str] = None

    def __str__(self):
        result = "/".join(
            [
                self.area or "",
                self.section or "",
                self.name or "",
            ]
        )
        return result.strip("/ ")


@dataclass
class FileLocation:
    file: str
    packages: list[FileLocationPackage] = field(default_factory=list)

    def __str__(self):
        return f"{self.file} {','.join([str(i) for i in self.packages])}"
