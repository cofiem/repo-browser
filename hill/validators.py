from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class HexadecimalValidator:
    """Validate that the string contains only hexadecimal characters."""

    message = _("Only hexadecimal characters (0 - 9 and a - f) are allowed.")
    code = "hexadecimal_only"

    def __init__(self, prefix_separator: str = None, message=None, code=None):
        self.prefix_separator = prefix_separator
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code

    def __call__(self, value):
        hex_value = str(value)
        if self.prefix_separator is not None:
            hex_value = str(value).split(maxsplit=1)[-1]

        try:
            int(hex_value, 16)
        except ValueError:
            raise ValidationError(self.message, code=self.code, params={"value": value})

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.message == other.message
            and self.code == other.code
        )
