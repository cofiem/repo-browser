from django import forms


class RepositoryForm(forms.Form):
    url = forms.URLField(label="Repository Url", required=True)


