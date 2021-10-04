from enum import Enum
from typing import Optional, Any

from django.core.cache import caches


class LocalCacheTime(Enum):
    """
    Enumeration of available cache times.

    - DONT_CACHE - don't cache.
    - KEEP - cache without expiry
    - others are the number of seconds in the given time period
    """

    DONT_CACHE = 0
    KEEP = 1
    FIVE_MINUTES = 300
    THIRTY_MINUTES = 1800
    ONE_DAY = 86400
    ONE_WEEK = 604800
    ONE_MONTH = 2629800


class LocalCache:
    """A local cache."""

    def __init__(self, cache_alias: str = "default"):
        self._cache_alias = cache_alias
        if cache_alias:
            self._cache = caches[cache_alias]
        else:
            self._cache = None

    def get(
        self, key: str, default=None, version: Optional[int] = None
    ) -> tuple[bool, Any]:
        """Retrieve a value from the cache."""
        # If you need to determine whether the object exists in the cache and
        # you have stored a literal value None,
        # use a sentinel object as the default.
        sentinel = object()
        result = self._cache.get(
            key=key,
            default=sentinel if default is None else default,
            version=version,
        )
        if result is sentinel:
            return False, None
        return True, result

    def set(
        self,
        key: str,
        value: Any,
        cache_time: LocalCacheTime = LocalCacheTime.KEEP,
        version: Optional[int] = None,
    ) -> None:
        """Store a value in the cache."""

        return self._cache.set(
            key=key,
            value=value,
            timeout=self._get_cache_timeout(cache_time),
            version=version,
        )

    def get_or_set(
        self,
        key: str,
        value: Any,
        cache_time: LocalCacheTime = LocalCacheTime.KEEP,
        version: Optional[int] = None,
    ) -> Any:
        """Store a value if there is no existing value, then retrieve it."""
        return self._cache.get_or_set(
            key=key,
            default=value,
            timeout=self._get_cache_timeout(cache_time),
            version=version,
        )

    def clear(self):
        """Empty the cache."""
        return self._cache.clear()

    def _get_cache_timeout(self, cache_time: LocalCacheTime):
        if cache_time == LocalCacheTime.DONT_CACHE:
            # A timeout of 0 won’t cache the value.
            return 0

        if cache_time == LocalCacheTime.KEEP:
            # Passing in None for timeout will cache the value forever.
            return None

        return cache_time.value
