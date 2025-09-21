from urllib.parse import parse_qs, quote_plus, unquote, urlsplit, urlunsplit, quote

import attrs
from beartype import beartype


@beartype
def to_url(scheme: str, netloc: str, *args: str | None, **kwargs: str | None) -> str:
    if not netloc:
        raise AptException("Must provide netloc.")
    if not scheme:
        scheme = "https"

    if args:
        path = "/".join(quote(arg) for arg in args if str(arg or "").strip())
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
    scheme: str | None = None
    netloc: str | None = None
    path: list[str] | None = None
    query: dict[str, list[str]] | None = None

    @property
    def path_str(self) -> str:
        return "/".join(self.path or [])

    @property
    def url(self):
        return to_url(
            self.scheme, self.netloc, *(self.path or []), **(self.query or {})
        )


@beartype
def from_url(url: str) -> SimpleUrl:
    if "//" not in url:
        # urlsplit requires '//' in the url to recognise a netloc
        url = f"//{url}"
    parts = urlsplit(url)
    result = SimpleUrl(
        scheme=parts.scheme,
        netloc=parts.netloc,
        path=[unquote(p) for p in parts.path.split("/") if p and p.strip()],
        query=parse_qs(parts.query),
    )
    return result


@beartype
def build_url(base: str, path: list[str]) -> str:
    parts = from_url(base)
    url = to_url(parts.scheme, parts.netloc, *parts.path, *path)
    return url


@beartype
class AptException(ValueError):
    pass
