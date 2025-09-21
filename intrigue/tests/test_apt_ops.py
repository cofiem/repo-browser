import unittest

from intrigue.apt.models import RepositorySourceEntry
from intrigue.apt.operations import parse_repository
from intrigue.apt.resource import AptRepoKnownNames
from intrigue.apt.utils import SimpleUrl


class TestAptOperations(unittest.TestCase):
    def test_parse_repository_invalid(self):
        # empty
        self.assertRaisesRegex(
            ValueError,
            "The repository or url domain must be provided.",
            lambda: parse_repository(),
        )

        # different domains
        repository = "testing-repository.example.com"
        url_netloc = "testing-url.example.com"
        self.assertRaisesRegex(
            ValueError,
            f"The url domain '{url_netloc}' must match the repository '{repository}'.",
            lambda: parse_repository(url=url_netloc, repository=repository),
        )

        # different paths
        directory = "example/one/two"
        url_path = "example/three/four"
        self.assertRaisesRegex(
            ValueError,
            f"The url path '{url_path}' must match the directory '{directory}'.",
            lambda: parse_repository(
                url=f"{url_netloc}/{url_path}", directory=directory
            ),
        )

    def test_parse_repository(self):
        data: list[AptRepoKnownNames] = AptRepoKnownNames.from_resources_csv_file()
        self.assertEqual(
            [
                parse_repository(
                    **{
                        "url": item.url,
                        "distribution": item.distribution,
                        "component": item.component,
                        "architecture": item.architecture,
                        "sign_url": item.sign_url,
                    }
                )
                for item in data
            ],
            [
                RepositorySourceEntry(
                    url=SimpleUrl(
                        scheme="https",
                        netloc="ppa.launchpadcontent.net",
                        path=["deadsnakes", "ppa", "ubuntu"],
                        query={},
                    ),
                    distributions=["focal"],
                    components=["main"],
                    architectures=[],
                    signed_by=None,
                ),
                RepositorySourceEntry(
                    url=SimpleUrl(
                        scheme="https",
                        netloc="ppa.launchpadcontent.net",
                        path=["deadsnakes", "ppa", "ubuntu"],
                        query={},
                    ),
                    distributions=["focal"],
                    components=["main"],
                    architectures=[],
                    signed_by=None,
                ),
                RepositorySourceEntry(
                    url=SimpleUrl(
                        scheme="https",
                        netloc="download.docker.com",
                        path=["linux", "ubuntu"],
                        query={},
                    ),
                    distributions=["focal"],
                    components=["stable"],
                    architectures=["amd64"],
                    signed_by="https://download.docker.com/linux/ubuntu/gpg",
                ),
                RepositorySourceEntry(
                    url=SimpleUrl(
                        scheme="https",
                        netloc="nginx.org",
                        path=["packages", "ubuntu"],
                        query={},
                    ),
                    distributions=["focal"],
                    components=["stable"],
                    architectures=["amd64"],
                    signed_by="https://nginx.org/keys/nginx_signing.key",
                ),
                RepositorySourceEntry(
                    url=SimpleUrl(
                        scheme="https",
                        netloc="apt.postgresql.org",
                        path=["pub", "repos", "apt"],
                        query={},
                    ),
                    distributions=["focal-pgdg"],
                    components=["main"],
                    architectures=["amd64"],
                    signed_by="https://www.postgresql.org/media/keys/ACCC4CF8.asc",
                ),
                RepositorySourceEntry(
                    url=SimpleUrl(
                        scheme="https",
                        netloc="apt.releases.hashicorp.com",
                        path=[],
                        query={},
                    ),
                    distributions=["focal"],
                    components=["main"],
                    architectures=["amd64", "arm64"],
                    signed_by="https://apt.releases.hashicorp.com/gpg",
                ),
                RepositorySourceEntry(
                    url=SimpleUrl(
                        scheme="https",
                        netloc="dl.google.com",
                        path=["linux", "chrome", "deb"],
                        query={},
                    ),
                    distributions=[],
                    components=[],
                    architectures=[],
                    signed_by="https://dl.google.com/linux/linux_signing_key.pub",
                ),
                RepositorySourceEntry(
                    url=SimpleUrl(
                        scheme="https",
                        netloc="old-releases.ubuntu.com",
                        path=["ubuntu"],
                        query={},
                    ),
                    distributions=[],
                    components=[],
                    architectures=[],
                    signed_by=None,
                ),
                RepositorySourceEntry(
                    url=SimpleUrl(
                        scheme="https",
                        netloc="repo.jellyfin.org",
                        path=["ubuntu"],
                        query={},
                    ),
                    distributions=["noble"],
                    components=["main"],
                    architectures=["amd64"],
                    signed_by="https://repo.jellyfin.org/jellyfin_team.gpg.key",
                ),
                RepositorySourceEntry(
                    url=SimpleUrl(
                        scheme="https",
                        netloc="mirror.aarnet.edu.au",
                        path=["pub", "linuxmint-packages"],
                        query={},
                    ),
                    distributions=["zara"],
                    components=["main"],
                    architectures=["amd64"],
                    signed_by="https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x302f0738f465c1535761f965a6616109451bbbf2",
                ),
                RepositorySourceEntry(
                    url=SimpleUrl(
                        scheme="https",
                        netloc="mirror.aarnet.edu.au",
                        path=["pub", "ubuntu", "archive"],
                        query={},
                    ),
                    distributions=["noble"],
                    components=["main"],
                    architectures=["amd64"],
                    signed_by="https://mirror.aarnet.edu.au/pub/ubuntu/archive/project/ubuntu-archive-keyring.gpg",
                ),
                RepositorySourceEntry(
                    url=SimpleUrl(
                        scheme="https",
                        netloc="mirror.aarnet.edu.au",
                        path=["pub", "debian"],
                        query={},
                    ),
                    distributions=["trixie"],
                    components=["main"],
                    architectures=["amd64"],
                    signed_by="https://ftp-master.debian.org/keys/archive-key-13.asc",
                ),
            ],
        )
