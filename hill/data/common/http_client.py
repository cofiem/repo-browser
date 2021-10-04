import requests
from django.utils.text import slugify

from hill.data.common.local_cache import LocalCache, LocalCacheTime
from hill.data.common.logger import Logger


class HttpClient:
    def __init__(self, logger: Logger, cache: LocalCache):
        self._logger = logger
        self._cache = cache
        self._headers = {
            "user-agent": "amass-repo-browser (+https://github.com/cofiem/repo-browser)"
        }

    def get(self, url: str, cache_time: LocalCacheTime = LocalCacheTime.KEEP):
        """HTTP GET"""
        key = self._key("get", url)
        found, result = self._cache.get(key)
        if found:
            return result

        result = requests.get(url, headers=self._headers)
        self._cache.set(key=key, value=result, cache_time=cache_time)
        return result

    def head(self, url: str, cache_time: LocalCacheTime = LocalCacheTime.KEEP):
        """HTTP HEAD"""
        key = self._key("head", url)
        found, result = self._cache.get(key)
        if found:
            return result

        result = requests.head(url, headers=self._headers)
        self._cache.set(key=key, value=result, cache_time=cache_time)
        return result

    def _key(self, prefix: str, value: str):
        return "-".join(["http-client", prefix, slugify(value)])
