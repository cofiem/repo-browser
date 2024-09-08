from django.urls import path

from . import views

app_name='discover'
urlpatterns = [
    path("", views.index, name="index"),
    path("repository/<repository>/", views.repository, name="repository"),
    path("directory/<repository>/<path:directory>/", views.directory, name="directory"),
    path("item/<repository>/<path:directory>/<item>/", views.item, name="item"),
    path("instance/<repository>/<path:directory>/<item>/<instance>/", views.instance, name="instance"),
]