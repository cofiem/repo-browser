from dataclasses import dataclass, field

from hill.data.apt.item.paragraph import Paragraph


@dataclass
class Control:
    """
    A Debian control file.

    Ref: https://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-package
    """

    paragraphs: list[Paragraph] = field(default_factory=list)

    def __str__(self):
        return f"{len(self.paragraphs)} items"
