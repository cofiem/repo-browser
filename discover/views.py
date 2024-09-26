from django.conf import settings
from django.http import HttpResponseRedirect, QueryDict
from django.urls import reverse, NoReverseMatch
from django.views import generic

from discover.forms import RepositoryForm
from intrigue.apt import (
    find,
    models as apt_models,
    utils as apt_utils,
    operations as apt_operations,
)
from intrigue.apt.landmark import KnownItem
from intrigue.gpg import message_armor_radix64, message_native


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
        try:
            url = reverse("discover:repository", kwargs={"repository": parts.netloc, "directory": parts.path_str})
        except NoReverseMatch:
            url = reverse("discover:repository-netloc", kwargs={"repository": parts.netloc})

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

        repo_src = apt_operations.parse_repository(
            url=apt_utils.to_url("https", repository, directory),
            distributions=kwargs.get("distribution") or request.GET.get("distribution") or None,
            components=kwargs.get("component") or request.GET.get("component") or None,
            architectures=kwargs.get("architecture") or request.GET.get("architecture") or None,
            signed_by=kwargs.get("signed") or request.GET.get("sign_url") or None,
        )

        html_listing = find.get_links(client, repo_src.url)
        dist = repo_src.distributions[0] if repo_src.distributions else 'jammy'
        release_info = find.release(client, repo_src, dist)
        if release_info:
            info = release_info.get(KnownItem.RELEASE_COMBINED.value)
            info_url = info.get('url')
            info_content = info.get('content')

            gpg_msg = message_armor_radix64.read(info_content)
            gpg_sig = message_native.read(gpg_msg.signature.data)

            release_data = apt_operations.release(info_url, gpg_msg.signed_message.text)

            if repo_src.signed_by:
                gpg_key_result, gpg_key_content = client.get_raw(repo_src.signed_by)
                gpg_key = message_armor_radix64.read(gpg_key_content)
            else:
                gpg_key = None

            # apt_models.RepositoryRelease(
            #     release = release_data,
            #     signature=gpg_sig.signature,
            #     public_key=gpg_key,
            # )

        else:
            release_data = None
            gpg_key = None
        # found_url, landmark = find.detect_landmarks(client, repo_src)

        # TODO: get each item async and show any file content?
        # TODO: if exactly one dist is provided, build the url including it

        context = self.get_context_data(**kwargs)
        # context["repo_Src"] = repo_Src
        # context["dists"] = dists
        # context["comps"] = comps
        # context["archs"] = archs
        context["html_listing"] = html_listing
        context["directory"] = directory or '/'
        context["release_info"] = release_info
        context["release_data"] = release_data
        context["gpg_key"] = gpg_key
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
