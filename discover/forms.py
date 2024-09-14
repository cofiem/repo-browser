from django import forms


class RepositoryForm(forms.Form):
    template_name = "discover/repository_form.html"
    url = forms.CharField(
        label="Repository Url",
        required=True,
        help_text="Url for the base of the distribution or a Debian repository one-line list style format.",
        widget=forms.TextInput(attrs={"class": "form-control"}),
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
