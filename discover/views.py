from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect, QueryDict
from django.urls import reverse
from django.views import generic

from discover.forms import RepositoryForm
from intrigue.apt import find, models as apt_models, utils as apt_utils


class IndexView(generic.FormView):
    """Home page."""

    template_name = "discover/index.html"
    form_class = RepositoryForm

    def form_valid(self, form):
        # build base url
        parts = apt_utils.from_url(form.cleaned_data.get("url"))
        kwargs = {
            "repository": parts.netloc,
            "directory": parts.path,
        }
        url = reverse("discover:repository", kwargs=kwargs)

        # add query if available
        query = QueryDict(
            {
                "sign_url": form.cleaned_data.get("sign_url"),
                "distribution": form.cleaned_data.get("distribution"),
                "component": form.cleaned_data.get("component"),
                "architecture": form.cleaned_data.get("architecture"),
            }
        )
        if query:
            url += "?" + query.urlencode()

        return HttpResponseRedirect(url)


class RepositoryView(generic.TemplateView):
    """Top level of a repository."""

    template_name = "discover/repository.html"

    def get(self, request, *args, **kwargs):
        repository = kwargs.get("repository")
        directory = kwargs.get("directory")
        client = settings.BACKEND_HTTP_CLIENT
        apt_src = apt_models.RepositorySourceEntry(
            url=apt_utils.to_url("https", repository, directory),
            distributions=kwargs.get("distribution", "").split(" "),
            components=kwargs.get("component", "").split(" "),
            architectures=kwargs.get("architecture", "").split(" "),
            signed_by=kwargs.get("signed"),
        )

        html_listing = find.get_links(client, apt_src.url)

        # TODO: get each item async and show any file content?

        context = self.get_context_data(**kwargs)
        # context["apt_src"] = apt_src
        # context["dists"] = dists
        # context["comps"] = comps
        # context["archs"] = archs
        context["html_listing"] = html_listing
        return self.render_to_response(context)


class ItemView(generic.TemplateView):
    """An item with one or more specific instances."""

    template_name = "discover/item.html"

    def get(self, request, *args, **kwargs):
        repository = kwargs.get("repository")
        directory = kwargs.get("directory")
        item = kwargs.get("item")

        url = apt_utils.to_url("https", repository, directory, item)

        context = self.get_context_data(**kwargs)
        context["url"] = url
        return self.render_to_response(context)
