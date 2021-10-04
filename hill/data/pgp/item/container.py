from dataclasses import dataclass, field

from hill.data.pgp.item.message import Message


@dataclass
class Container:

    messages: list[Message] = field(default_factory=list)

    def __str__(self):
        return ", ".join([i.name for i in self.messages])
