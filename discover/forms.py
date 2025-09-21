from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, RegexValidator
from django.utils.translation import gettext_lazy as _

from intrigue.apt.operations import RE_LIST_ENTRY


def validate_url_or_deb(value):
    is_url = False
    is_deb = False
    try:
        URLValidator()(value)
        is_url = True
    except ValidationError:
        pass

    try:
        RegexValidator(regex=RE_LIST_ENTRY)(value)
        is_deb = True
    except ValidationError:
        pass

    if not is_url and not is_deb:
        raise ValidationError(
            _("Must be a URL or DEB one-line-style list format"),
            code="not-url-or-deb",
        )


class RepositoryForm(forms.Form):
    template_name = "discover/repository_form.html"
    url = forms.CharField(
        label="Repository Url",
        required=True,
        help_text="Url for the base of the distribution or a Debian repository one-line list style format.",
        widget=forms.TextInput(attrs={"class": "form-control"}),
        validators=[validate_url_or_deb],
    )
    distribution = forms.CharField(
        label="Distribution Names",
        required=False,
        help_text="Zero, one, or more space separated distribution names.",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    component = forms.CharField(
        label="Component Names",
        required=False,
        help_text="Zero, one, or more space separated component names.",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    architecture = forms.CharField(
        label="Architecture Names",
        required=False,
        help_text="Zero, one, or more space separated architecture names.",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    sign_url = forms.URLField(
        label="Signed By Url",
        required=False,
        help_text="Url to the public key used to sign the repository contents.",
        widget=forms.URLInput(attrs={"class": "form-control"}),
    )

    def is_valid(self):
        # loop on *all* fields if key '__all__' found else only on errors:
        for x in self.fields if "__all__" in self.errors else self.errors:
            attrs = self.fields[x].widget.attrs
            attrs.update({"class": attrs.get("class", "") + " is-invalid"})
        return super().is_valid()
