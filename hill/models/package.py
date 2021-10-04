import urllib.parse
from django.db import models

from hill.fields import HashField
from hill.models import Repository
from hill.models.abstract_base import AbstractBase


class Package(AbstractBase):
    """Details for a resource that provides a particular package version."""

    OPERATING_SYSTEMS = (
        ("ubuntu-1404", "Ubuntu 14.04 LTS Trusty Tahr"),
        ("ubuntu-1410", "Ubuntu 14.10 Utopic Unicorn"),
        ("ubuntu-1504", "Ubuntu 15.04 Vivid Vervet"),
        ("ubuntu-1510", "Ubuntu 15.10 Wily Werewolf"),
        ("ubuntu-1604", "Ubuntu 16.04 LTS Xenial Xerus"),
        ("ubuntu-1610", "Ubuntu 16.10 Yakkety Yak"),
        ("ubuntu-1704", "Ubuntu 17.04 Zesty Zapus"),
        ("ubuntu-1710", "Ubuntu 17.10 Artful Aardvark"),
        ("ubuntu-1804", "Ubuntu 18.04 LTS Bionic Beaver"),
        ("ubuntu-1810", "Ubuntu 18.10 Cosmic Cuttlefish"),
        ("ubuntu-1904", "Ubuntu 19.04 Disco Dingo"),
        ("ubuntu-1910", "Ubuntu 19.10 Eoan Ermine"),
        ("ubuntu-2004", "Ubuntu 20.04 LTS Focal Fossa"),
        ("ubuntu-2010", "Ubuntu 20.10 Groovy Gorilla"),
        ("ubuntu-2104", "Ubuntu 21.04 Hirsute Hippo"),
        ("ubuntu-2110", "Ubuntu 21.10 Impish Indri"),
    )

    ARCHITECTURES = (
        ("x86-64", "64-bit x86"),
        ("x86-32", "32-bit x86"),
        ("arm-64", "64-bit arm"),
    )

    # relations
    repository = models.ForeignKey(
        Repository,
        on_delete=models.CASCADE,
        help_text="The repository containing this package.",
    )

    # fields
    name = models.CharField(
        max_length=500,
        help_text="The package name.",
    )
    version = models.CharField(
        max_length=100,
        help_text="The package version.",
    )
    operating_system = models.CharField(
        max_length=20,
        choices=OPERATING_SYSTEMS,
        help_text="The operating system this package supports.",
    )
    architecture = models.CharField(
        max_length=10,
        choices=ARCHITECTURES,
        help_text="The architecture this package supports.",
    )
    download_size = models.BigIntegerField(
        blank=True,
        help_text="The file size of the download in bytes.",
    )
    installed_size = models.BigIntegerField(
        blank=True,
        help_text="The size of the installed package in bytes.",
    )
    description = models.TextField(
        blank=True,
        help_text="A description of the contents and purpose of this package.",
    )
    home_url = models.URLField(
        blank=True,
        help_text="Absolute url to the home page for this package.",
    )
    download_url = models.URLField(
        help_text="Relative url to the package file.",
    )
    hash_md5 = HashField(
        algorithm="md5",
        blank=True,
    )
    hash_sha1 = HashField(
        algorithm="sha1",
        blank=True,
    )
    hash_sha256 = HashField(
        algorithm="sha256",
        blank=True,
    )
    hash_sha512 = HashField(
        algorithm="sha512",
        blank=True,
    )

    class Meta:
        # todo: unique together: repository & name & version & operating_system & architecture
        ordering = ["name", "version", "modified_date"]

    def __str__(self):
        return f"{self.name} ({self.version})"

    def full_download_url(self):
        return urllib.parse.urljoin(self.repository.download_url, self.download_url)
