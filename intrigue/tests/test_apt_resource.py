import unittest

from intrigue.apt.resource import AptRepoKnownNames, KnownNames


class TestAptResource(unittest.TestCase):
    def test_repo_names(self):
        data = list(AptRepoKnownNames.from_resources_csv_file())
        self.assertEqual(len(data), 12)

    def test_known_names(self):
        data = list(KnownNames.from_resources_csv_file())
        self.assertEqual(len(data), 84)
