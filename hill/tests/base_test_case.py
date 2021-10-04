import importlib.resources
from dataclasses import dataclass, fields
from typing import Any

from django.test import TestCase

from hill.data.apt.item.package_relation import PackageRelation
from hill.data.apt.item.package_tag import PackageTag


class BaseTestCase(TestCase):
    def _read_text(self, name: str):
        package = "hill.tests.resources"
        resource = name
        content = importlib.resources.read_text(package, resource)
        return content

    def _display_dataclass(self, obj):
        result = {}
        for f in fields(obj):
            name = f.name
            value = getattr(obj, f.name)
            if not value:
                continue
            elif isinstance(value, str):
                result[name] = value
            elif isinstance(value, list):
                result[name] = self._display_list(value)
            elif isinstance(value, dict):
                result[name] = len(value)
            else:
                result[name] = value
        return result

    def _display_list(self, obj: list):
        result = []
        for item in obj:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, PackageTag):
                return PackageTag.display(obj)
            elif isinstance(item, PackageRelation):
                return PackageRelation.display(obj)
            elif isinstance(item, list):
                for sub_item in item:
                    if isinstance(sub_item, PackageRelation):
                        return PackageRelation.display(obj)
                result.append(item)
            else:
                result.append(None)
        if all([i is None for i in result]):
            return len(obj)
        else:
            return result

    def _assert_equal_all(self, data: list[tuple[Any, Any]]):
        for actual, expected in data:
            self.assertEqual(expected, actual)
