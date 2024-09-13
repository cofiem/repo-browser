from collections import namedtuple
from urllib.parse import urlsplit, urlunsplit, quote_plus, unquote, parse_qs


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


SimpleUrl = namedtuple("SimpleUrl", ["scheme", "netloc", "path", "query"])


def from_url(url: str) -> SimpleUrl:
    parts = urlsplit(url)
    result = SimpleUrl(
        parts.scheme,
        parts.netloc,
        [unquote(p) for p in parts.path.split("/") if p and p.strip()],
        parse_qs(parts.query),
    )
    return result
