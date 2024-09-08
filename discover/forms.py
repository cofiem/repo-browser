from django import forms


class RepositoryForm(forms.Form):
    url = forms.URLField(label="Repository Url", required=True)
    sign_url = forms.URLField(label="Signed By Url", required=False)
    distribution = forms.CharField(label="Distribution Names", required=False, help_text="Zero, one, or more space separated distribution names.")
    component = forms.CharField(label="Component Names", required=False, help_text="Zero, one, or more space separated component names.")
    architecture = forms.CharField(label="Architecture Names", required=False, help_text="Zero, one, or more space separated architecture names.")


