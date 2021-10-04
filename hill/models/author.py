from django.db import models

from hill.models.abstract_base import AbstractBase


class Author(AbstractBase):
    """A package author."""

    name = models.CharField(
        max_length=500,
        help_text="The author name.",
    )
    email = models.EmailField(
        blank=True,
        help_text="The email address.",
    )

    class Meta:
        ordering = ["name", "modified_date"]

    def __str__(self):
        return self.name
