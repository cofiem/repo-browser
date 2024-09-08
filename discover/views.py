import http
from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
from django.views import generic

from discover.forms import RepositoryForm
from intrigue.models import HtmlListing


class IndexView(generic.FormView):
    """Home page."""
    template_name = 'discover/index.html'
    form_class = RepositoryForm

    def form_valid(self, form):
        parts = urlsplit(form.cleaned_data.get("url"))
        return HttpResponseRedirect(reverse("discover:repository", args=(parts.netloc, parts.path.strip('/'))))


class RepositoryView(generic.TemplateView):
    """Top level of a repository."""
    template_name = 'discover/repository.html'

    def _get_links(self, url: str):
        status, html = settings.BACKEND_HTTP_CLIENT.get_text(url)
        if status == http.HTTPStatus.OK:
            return HtmlListing.from_html(url, html)

        if status == http.HTTPStatus.NOT_FOUND:
            raise Http404()

        raise ValueError()

    def get(self, request, *args, **kwargs):
        repository = kwargs.get('repository')
        directory = kwargs.get('directory')

        url = settings.BACKEND_HTTP_CLIENT.build_url(repository, directory)
        links = self._get_links(url)

        context = self.get_context_data(**kwargs)
        context['links'] = links
        return self.render_to_response(context)

class ItemView(generic.TemplateView):
    """An item with one or more specific instances."""
    template_name = 'discover/item.html'

    def get(self, request, *args, **kwargs):
        repository = kwargs.get('repository')
        directory = kwargs.get('directory')
        item = kwargs.get('item')

        url = settings.BACKEND_HTTP_CLIENT.build_url(repository, directory, item)

        context = self.get_context_data(**kwargs)
        context['url'] = url
        return self.render_to_response(context)