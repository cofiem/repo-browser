from dataclasses import dataclass


@dataclass
class FileHash:

    hash_value: str
    size_bytes: int
    name: str

    def __str__(self):
        return " ".join([self.name, self.size_bytes, self.hash_value])
