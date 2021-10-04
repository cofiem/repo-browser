from typing import Iterable, Optional

from hill.data.common.http_client import HttpClient
from hill.data.common.logger import Logger
from hill.data.pgp.item.message import Message


class AptClient:
    """
    Access and parse an apt repository.

    Specification: https://wiki.debian.org/DebianRepository/Format
    """

    def __init__(
        self,
        logger: Logger,
        http_client: HttpClient,
        base_url: str,
        pgp_public_key: Optional[Message],
    ):
        self._logger = logger
        self._http_client = http_client
        self._base_url = base_url
        self._pgp_public_key = pgp_public_key

    def get(self):
        """Get information about a repository."""
        distributions = self.get_distribution_names()

        if not distributions:
            self._logger.warning(f"Found no distribution names.")
            return self.get_flat()

        all_releases = []
        all_contents = []
        all_packages = []
        all_translations = []

        # for distribution in distributions:
        #     release = self.get_release_file(distribution)
        #     all_releases.append(release)
        #
        #     for component in release.components:
        #         for architecture in release.architectures:
        #             self.get_contents_file(distribution, component, architecture)
        return {
            "releases": all_releases,
            "packages": all_packages,
            "contents": all_contents,
            "translations": all_translations,
        }

    def get_flat(self):
        release_url, packages_url = self.get_flat_dir_files()

        releases = []
        packages = []
        if not release_url and not packages_url:
            self._logger.warning(f"Found no flat repository files.")
            return {
                "releases": releases,
                "packages": packages,
                "contents": [],
                "translations": [],
            }

        # if release_url:
        #     raw = self._http_client.get(release_url)
        #     if raw.ok:
        #         releases.append(ReleaseFile.from_lines(raw.text))
        #

        # if packages_url:
        #     raw = self._http_client.get(packages_url)
        #     if raw.ok:
        #         packages.append(PackagesFile.from_lines(raw.text))

        return {
            "releases": releases,
            "packages": packages,
            "contents": [],
            "translations": [],
        }

    def get_distribution_names(self) -> Iterable[str]:
        """
        Get a list of files and directories from the
        $ARCHIVE_ROOT/dists directory.
        Assume all items in this directory are distribution names.
        """

        return []

    def get_flat_dir_files(self):
        """
        Assume a 'flat repository format' and get the known files from the $ARCHIVE_ROOT directory.
        """
        packages_url = ""
        release_url = ""
        return release_url, packages_url
