from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "discover"
urlpatterns = [
    path(
        "",
        views.IndexView.as_view(),
        name="index",
    ),
    path(
        "repository/<repository>/<path:directory>/",
        views.RepositoryView.as_view(),
        name="repository",
    ),
    path(
        "repository/<repository>/",
        views.RepositoryView.as_view(),
        name="repository-netloc",
    ),
    path(
        "repository/",
        RedirectView.as_view(url="", permanent=False),
        name="repository-to-index",
    ),
]
