import uuid

from hill.data.common.local_cache import LocalCache
from hill.tests.base_test_case import BaseTestCase


class LocalCacheTestCase(BaseTestCase):
    def setUp(self) -> None:
        self._cache = LocalCache()

    def tearDown(self) -> None:
        self._cache.clear()

    def test_get_miss(self):
        found, result = self._cache.get("something")
        self.assertFalse(found)
        self.assertIsNone(result)

    def test_get_hit(self):
        key = str(uuid.uuid4())
        value = str(uuid.uuid4())

        self._cache.set(key, value)
        found, result = self._cache.get(key)
        self.assertTrue(found)
        self.assertEqual(value, result)

    def test_get_or_set_miss(self):
        key = str(uuid.uuid4())
        value = str(uuid.uuid4())

        result = self._cache.get_or_set(key, value)
        self.assertEqual(value, result)

    def test_get_or_set_hit(self):
        key = str(uuid.uuid4())
        value = str(uuid.uuid4())

        self._cache.set(key, value)
        result = self._cache.get_or_set(key, value)
        self.assertEqual(value, result)
