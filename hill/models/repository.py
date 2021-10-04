from django.db import models

from hill.models.abstract_base import AbstractBase


class Repository(AbstractBase):
    """A collection of Packages."""

    name = models.CharField(max_length=500, help_text="The repository name.")
    download_url = models.URLField(help_text="Absolute url to the home page.")
    home_url = models.URLField()

    class Meta:
        ordering = ["name", "modified_date"]

    def __str__(self):
        return self.name
