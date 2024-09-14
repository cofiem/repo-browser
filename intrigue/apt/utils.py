from collections import namedtuple
from urllib.parse import urlsplit, urlunsplit, quote_plus, unquote, parse_qs

import attrs
from beartype import beartype


def to_url(scheme: str, netloc: str, *args: str, **kwargs: str) -> str:
    if not netloc:
        raise ValueError("Must provide netloc.")
    if not scheme:
        scheme = "https"

    if args:
        path = "/".join((arg for arg in args if str(arg or "").strip()))
    else:
        path = ""

    query = "&".join(
        [f"{quote_plus(k)}={quote_plus(v)}" for k, v in (kwargs or {}).items()]
    )
    parts = (scheme, netloc, path, query, "")
    result = urlunsplit(parts)
    return result

@beartype
@attrs.frozen
class SimpleUrl:
    scheme:str
    netloc: str
    path: list[str]
    query: dict[str, list[str]]

    @property
    def path_str(self) -> str:
        return '/'.join(self.path)


def from_url(url: str) -> SimpleUrl:
    parts = urlsplit(url)
    result = SimpleUrl(
        parts.scheme,
        parts.netloc,
        [unquote(p) for p in parts.path.split("/") if p and p.strip()],
        parse_qs(parts.query),
    )
    return result
