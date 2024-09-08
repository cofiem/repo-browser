from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    """Home page."""
    return HttpResponse("Repo Browser home page.")

def repository(request, repository):
    """Top level of a repository."""
    return HttpResponse("Repository home page.")

def directory(request, repository, directory):
    """A directory within a repository."""
    return HttpResponse("Repository directory page.")

def item(request, repository, directory, item):
    """An item with one or more specific instances."""
    return HttpResponse("Item page.")

def instance(request, repository, directory, item, instance):
    """An instance of an item."""
    return HttpResponse("Instance page.")
