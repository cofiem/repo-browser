"""Manages web requests."""



import datetime
import logging
import pathlib
import time
import typing

import attrs
import parsel
import requests_cache
from beartype import beartype

from intrigue.apt import utils

logger = logging.getLogger(__name__)


@beartype
@attrs.frozen
class HtmlListing:
    """A html page that lists the contents of a directory."""

    url: str
    links: list[str]

    @property
    def urls(self):
        for link in self.links:
            yield utils.build_url(self.url, [link])


@beartype
class HttpClient:
    """A http client and cache using requests_cache."""

    _backend_file: pathlib.Path
    _backend: requests_cache.SQLiteCache

    _expire_after: datetime.timedelta
    _session: requests_cache.CachedSession

    _throttle_time: datetime.timedelta

    user_agent = "repo-browser (+https://github.com/cofiem/repo-browser)"

    def __init__(
            self,
            cache_file: typing.Optional[pathlib.Path],
            expire_after: typing.Optional[datetime.timedelta] = None,
            throttle_time: typing.Optional[datetime.timedelta] = None,
            use_cache_control: bool = False,
    ):
        if not cache_file:
            raise ValueError("Cache path must be provided.")

        self._backend_file = cache_file
        self._backend = requests_cache.SQLiteCache(self._backend_file)
        self._use_cache_control = use_cache_control

        if self._use_cache_control and expire_after is not None:
            self._expire_after = expire_after
        elif self._use_cache_control and expire_after is None:
            self._expire_after = datetime.timedelta(hours=2)
        else:
            self._expire_after = requests_cache.NEVER_EXPIRE

        self._session = requests_cache.CachedSession(
            backend=self._backend,
            expire_after=self._expire_after,
            cache_control=self._use_cache_control,
        )

        self._throttle_time = (
            throttle_time
            if throttle_time is not None
            else datetime.timedelta(seconds=1)
        )

        def _http_client_make_throttle_hook(timeout_seconds: float):
            """
            Make a request hook function
            that adds a custom delay for non-cached requests
            """

            def hook(response, *_args, **_kwargs):
                is_cached = getattr(response, "from_cache", False)
                if is_cached:
                    logger.debug(f"From cache {response.status_code}: {response.url}")
                else:
                    logger.debug(f"New response {response.status_code}: {response.url}")
                    time.sleep(timeout_seconds)

                return response

            return hook

        self._session.hooks["response"].append(
            _http_client_make_throttle_hook(self._throttle_time.total_seconds())
        )

    @property
    def session(self) -> requests_cache.CachedSession:
        return self._session

    def get_text(self, url: str) -> tuple[int, str | None]:
        resp = self.session.get(url)
        status = resp.status_code
        return status, resp.text if status < 400 else None

    def get_raw(self, url: str) -> tuple[int, bytes | None]:
        resp = self.session.get(url)
        status = resp.status_code
        return status, resp.content if status < 400 else None

    def get_json(self, url: str) -> tuple[int, list | dict | None]:
        resp = self.session.get(url)
        status = resp.status_code
        return status, resp.json() if status < 400 else None

    def from_html(self, url: str, html: str) -> HtmlListing:
        selector = parsel.Selector(text=html)

        links = []

        logger.debug("html listing links on %s", url)
        seen_parent = False
        options = ["..", "../", "parent directory"]
        for link in selector.css("a"):
            name = link.css("::text").get().strip().casefold()
            link_url = link.attrib["href"]
            logger.debug("html listing link: %s - %s", name, link_url)
            if not seen_parent and name not in options and link_url not in options:
                logger.debug("html listing link ignore: %s - %s", name, link_url)
                continue
            elif name in options or link_url in options:
                seen_parent = True
                logger.debug("html listing link parent: %s - %s", name, link_url)
                continue
            elif link_url.startswith("http") and not link_url.startswith(url):
                logger.debug(
                    "html listing link ignore external: %s - %s", name, link_url
                )
                continue
            else:
                links.append(link_url.strip())

        if seen_parent is not True:
            raise ValueError("Unknown html directory listing format.")

        return HtmlListing(url=url, links=sorted(links))
