from django.http import HttpResponseRedirect
from django.views import generic

from discover.applib import view_helper
from discover.forms import RepositoryForm
from intrigue.apt import (
    operations as apt_operations,
)
from intrigue.apt.resource import AptRepoKnownNames


def _to_repo(request, **kwargs):
    repo = apt_operations.parse_repository(**kwargs)
    return view_helper.repo_view_info(repo)


class IndexView(generic.FormView):
    """Home page."""

    template_name = "discover/index.html"
    form_class = RepositoryForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["examples"] = list(AptRepoKnownNames.from_resources_csv_file())
        return context

    def form_invalid(self, form):
        return super().form_invalid(form)

    def form_valid(self, form):
        view_info = _to_repo(
            self.request,
            **{
                "url": form.cleaned_data.get("url"),
                "distribution": form.cleaned_data.get("distribution"),
                "component": form.cleaned_data.get("component"),
                "architecture": form.cleaned_data.get("architecture"),
                "sign_url": form.cleaned_data.get("sign_url"),
            },
        )
        return HttpResponseRedirect(view_info["url"])


class RepositoryView(generic.TemplateView):
    """A path within a repository."""

    template_name = "discover/repository.html"

    def get(self, request, *args, **kwargs):
        view_info = _to_repo(
            request,
            **{
                "repository": self._get_value(request, kwargs, "repository"),
                "directory": self._get_value(request, kwargs, "directory"),
                "distribution": self._get_value(request, kwargs, "distribution"),
                "component": self._get_value(request, kwargs, "component"),
                "architecture": self._get_value(request, kwargs, "architecture"),
                "sign_url": self._get_value(request, kwargs, "sign_url"),
            },
        )
        context = self.get_context_data(**kwargs)
        context.update(view_info["view_context"])
        return self.render_to_response(context)

    def _get_value(self, request, get_kwargs, name: str) -> str | None:
        return get_kwargs.get(name) or request.GET.get(name) or None
