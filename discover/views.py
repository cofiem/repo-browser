from django.conf import settings
from django.http import HttpResponseRedirect, QueryDict
from django.urls import reverse
from django.views import generic

from discover.forms import RepositoryForm
from intrigue.apt import (
    find,
    models as apt_models,
    utils as apt_utils,
    operations as apt_operations,
)


class IndexView(generic.FormView):
    """Home page."""

    template_name = "discover/index.html"
    form_class = RepositoryForm

    def form_valid(self, form):
        param_url = form.cleaned_data.get("url")
        param_distribution = form.cleaned_data.get("distribution")
        param_component = form.cleaned_data.get("component")
        param_architecture = form.cleaned_data.get("architecture")
        param_sign_url = form.cleaned_data.get("sign_url")

        repo = apt_operations.parse_repository(
            param_url,
            param_distribution,
            param_component,
            param_architecture,
            param_sign_url,
        )

        parts = apt_utils.from_url(repo.url)
        kwargs = {
            "repository": parts.netloc,
            "directory": parts.path_str,
        }
        url = reverse("discover:repository", kwargs=kwargs)

        query = QueryDict(mutable=True)
        query.update(repo.as_querystring())
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
        # TODO: if exactly one dist is provided, build the url including it

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
