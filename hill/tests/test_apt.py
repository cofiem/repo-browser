import unittest
from datetime import datetime
from importlib import resources

from hill.data.apt.manage.controls import Controls
from hill.tests.base_test_case import BaseTestCase


class AptTestCase(BaseTestCase):
    def test_release_detached(self):
        package = "hill.tests.resources"
        resource_release = "debian-11-Release.txt"
        content_release = resources.read_text(package, resource_release)

        # TODO
        # resource_gpg = "debian-11-Release.gpg"
        # content_gpg = resources.read_text(package, resource_gpg)

        controls = Controls()
        control = controls.read_content(content_release)
        self.assertIsNotNone(control)
        self.assertEqual(1, len(control.paragraphs))

        f = self._display_dataclass(control.paragraphs[0])
        self.assertEqual(len(f), 13)
        self.maxDiff = None
        expected = {
            "origin": "Debian",
            "label": "Debian",
            "suite": "stable",
            "version": "11.0",
            "codename": "bullseye",
            "created_date": datetime(2021, 8, 14, 7, 57, 38),
            "acquire_by_hash": True,
            "architectures": [
                "all",
                "amd64",
                "arm64",
                "armel",
                "armhf",
                "i386",
                "mips64el",
                "mipsel",
                "ppc64el",
                "s390x",
            ],
            "components": ["main", "contrib", "non-free"],
            "description": "Debian 11.0 Released 14 August 2021",
            "ignored_fields": 2,
            "hash_files_md5": 582,
            "hash_files_sha256": 582,
        }
        self.assertDictEqual(f, expected)

    @unittest.skip("not implemented")
    def test_release_combined(self):
        package = "hill.tests.resources"
        resource = "debian-11-InRelease.txt"
        content = resources.read_text(package, resource)
        raise NotImplementedError()

    @unittest.skip("takes a long time")
    def test_package(self):
        package = "hill.tests.resources"
        resource = "debian-11-main-binary-all-Packages.xz"
        controls = Controls()
        self.maxDiff = None
        with resources.path(package, resource) as path:
            control = controls.read_file(path)

            for index, para in enumerate(control.paragraphs):
                if len(para.ignored_fields) > 0:
                    raise ValueError(para.ignored_fields)

            f = self._display_dataclass(control.paragraphs[0])
            self.assertEqual(len(f), 17)
            self.maxDiff = None
            expected = {
                "package": "0ad-data",
                "version": "0.0.23.1-1.1",
                "installed_size": 2044173,
                "maintainers": 1,
                "architectures": ["all"],
                "description": "Real-time strategy game of ancient warfare (data files)",
                "homepage_url": "http://play0ad.com/",
                "description_md5": "26581e685027d5ae84824362a4ba59ee",
                "section": "games",
                "priority": "optional",
                "filename": "pool/main/0/0ad-data/0ad-data_0.0.23.1-1.1_all.deb",
                "compressed_size": 701833824,
                "hash_md5": "b2b6e5510898abf0eee79da48995f92f",
                "hash_sha256": "afb3f0ddaceb36dc2d716d83d7fee4ada419511a948e4a06fa44bbc1b486e2c0",
                "tags": "role::app-data",
                "pre_depends": "dpkg (>= 1.15.6~)",
                "suggests": "0ad",
            }
            self.assertDictEqual(f, expected)

            f = self._display_dataclass(control.paragraphs[1])
            self.assertEqual(len(f), 21)
            self.maxDiff = None
            expected = {
                "package": "0ad-data-common",
                "source": "0ad-data",
                "version": "0.0.23.1-1.1",
                "installed_size": 2423,
                "maintainers": 1,
                "architectures": ["all"],
                "description": "Real-time strategy game of ancient warfare (common data files)",
                "homepage_url": "http://play0ad.com/",
                "description_md5": "8d014b839c4c4e9b6f82c7512d7e3496",
                "section": "games",
                "priority": "optional",
                "filename": "pool/main/0/0ad-data/0ad-data-common_0.0.23.1-1.1_all.deb",
                "compressed_size": 777612,
                "hash_md5": "49ad6a3a16eb34ea455bd3146a486aa0",
                "hash_sha256": "9bceebe75ab7bca79606aae24fd203681b10d1107b456a1a28f35c996d32199a",
                "replaces": "0ad-data (<< 0.0.12-1~)",
                "depends": "fonts-dejavu-core | ttf-dejavu-core, fonts-freefont-ttf | ttf-freefont, fonts-texgyre | tex-gyre",
                "pre_depends": "dpkg (>= 1.15.6~)",
                "suggests": "0ad",
                "breaks": "0ad-data (<< 0.0.12-1~)",
                "tags": "game::strategy, role::app-data, role::program, use::gameplaying",
            }
            self.assertDictEqual(f, expected)
