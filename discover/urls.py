from django.urls import path

from . import views

app_name = 'discover'
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("repository/<repository>/<path:directory>/", views.RepositoryView.as_view(), name="repository"),
    path("item/<repository>/<path:directory>/<item>/", views.ItemView.as_view(), name="item"),
]
