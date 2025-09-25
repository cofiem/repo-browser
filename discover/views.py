from django.http import HttpResponseRedirect
from django.views import generic

from discover.applib import view_helper
from discover.forms import RepositoryForm
from intrigue.apt import operations as apt_operations
from intrigue.apt.resource import AptRepoKnownNames


def _to_repo(**kwargs):
    repo = apt_operations.parse_repository(**kwargs)
    return view_helper.repo_view_info(repo)


def _get_value(request, get_kwargs, name: str) -> str | None:
    return get_kwargs.get(name) or request.GET.get(name) or None


class IndexView(generic.FormView):
    """Home page."""

    template_name = "discover/index.html"
    form_class = RepositoryForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["examples"] = list(AptRepoKnownNames.from_resources_csv_file())
        return context

    def form_valid(self, form):
        view_info = _to_repo(
            **{
                "url": form.cleaned_data.get("url"),
                "distribution": form.cleaned_data.get("distribution"),
                "component": form.cleaned_data.get("component"),
                "architecture": form.cleaned_data.get("architecture"),
                "sign_url": form.cleaned_data.get("sign_url"),
            },
        )
        return HttpResponseRedirect(view_info["url"])

    def get_initial(self):
        initial = super().get_initial()
        initial["url"] = _get_value(self.request, {}, "url")
        initial["distribution"] = _get_value(self.request, {}, "distribution")
        initial["component"] = _get_value(self.request, {}, "component")
        initial["architecture"] = _get_value(self.request, {}, "architecture")
        initial["sign_url"] = _get_value(self.request, {}, "sign_url")
        return initial


class RepositoryView(generic.TemplateView):
    """A path within a repository."""

    template_name = "discover/repository.html"

    def get(self, request, *args, **kwargs):
        view_info = _to_repo(
            **{
                "repository": _get_value(request, kwargs, "repository"),
                "directory": _get_value(request, kwargs, "directory"),
                "distribution": _get_value(request, kwargs, "distribution"),
                "component": _get_value(request, kwargs, "component"),
                "architecture": _get_value(request, kwargs, "architecture"),
                "sign_url": _get_value(request, kwargs, "sign_url"),
            },
        )
        context = self.get_context_data(**kwargs)
        context.update(view_info["view_context"] or {})
        return self.render_to_response(context)
