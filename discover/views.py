from urllib.parse import urlsplit

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect, QueryDict
from django.urls import reverse
from django.views import generic

from discover.forms import RepositoryForm
from intrigue.apt import find, models as apt_models


class IndexView(generic.FormView):
    """Home page."""
    template_name = 'discover/index.html'
    form_class = RepositoryForm

    def form_valid(self, form):
        # build base url
        parts = urlsplit(form.cleaned_data.get("url"))
        kwargs = {
            'repository': parts.netloc,
            'directory': parts.path.strip('/'),
        }
        url = reverse("discover:repository", kwargs=kwargs)

        # add query if available
        query = QueryDict({
            'sign_url': form.cleaned_data.get('sign_url'),
            'distribution': form.cleaned_data.get('distribution'),
            'component': form.cleaned_data.get('component'),
            'architecture': form.cleaned_data.get('architecture'),
        })
        if query:
            url += "?" + query.urlencode()

        return HttpResponseRedirect(url)


class RepositoryView(generic.TemplateView):
    """Top level of a repository."""
    template_name = 'discover/repository.html'

    def get(self, request, *args, **kwargs):
        repository = kwargs.get('repository')
        directory = kwargs.get('directory')
        client = settings.BACKEND_HTTP_CLIENT
        apt_src = apt_models.RepositorySourceEntry(
            url=client.build_url(repository, directory),
            distributions=kwargs.get('distribution', '').split(' '),
            components=kwargs.get('component', '').split(' '),
            architectures=kwargs.get('architecture', '').split(' '),
            signed_by=kwargs.get('signed'),
        )

        dists = find.distributions(client, apt_src)
        comps = find.components(client, apt_src)
        archs = find.architectures(client, apt_src)

        releases = []
        for dist in dists:
            releases.append(find.release(client, apt_src, dist))

        messages.info(request, request.META.get("REMOTE_ADDR"))

        context = self.get_context_data(**kwargs)
        context['html_listing'] = links
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
