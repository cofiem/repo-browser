import logging

from django.conf import settings
from django.http import QueryDict
from django.urls import reverse

from intrigue.apt import models as apt_models, find

logger = logging.getLogger(__name__)


def repo_view_info(repo: apt_models.RepositorySourceEntry | None):
    result = {"url": "", "view_context": {}}
    if not repo:
        return result

    # build the url for the page matching the repo
    if repo.url.path_str:
        url = reverse(
            "discover:repository",
            kwargs={"repository": repo.url.netloc, "directory": repo.url.path_str},
        )
    else:
        url = reverse(
            "discover:repository-netloc",
            kwargs={"repository": repo.url.netloc},
        )

    query = QueryDict(mutable=True)
    query.update(
        {
            "url": repo.url.url,
            "distribution": " ".join(repo.distributions or []),
            "component": " ".join(repo.components or []),
            "architecture": " ".join(repo.architectures or []),
            "sign_url": repo.signed_by or "",
        }
    )
    if query:
        url += "?" + query.urlencode()

    result["url"] = url
    result["view_context"]["repo_source_entry"] = repo

    client = settings.BACKEND_HTTP_CLIENT
    result["view_context"]["html_listing"] = find.get_links(client, repo.url.url)
    result["view_context"]["landmarks"] = find.detect_landmarks(repo)

    return result


# TODO:
# repo_src = apt_operations.parse_repository(
# url=apt_utils.to_url("https", repository, directory),
# distributions=
#        or request.GET.get("distribution")
#        or None,
# components=kwargs.get("component") or request.GET.get("component") or None,
# architectures=kwargs.get("architecture")
#           or request.GET.get("architecture")
#           or None,
# signed_by=kwargs.get("signed") or request.GET.get("sign_url") or None,
# )
#
# html_listing = find.get_links(client, repo_src.url)
# dist = repo_src.distributions[0] if repo_src.distributions else "jammy"
# release_info = None
# # release_info = find.release(client, repo_src, dist)
# # if release_info:
# if False:
# info = release_info.get(KnownItem.RELEASE_COMBINED.value)
# info_url = info.get("url")
# info_content = info.get("content")
#
# gpg_msg = message_armor_radix64.read(info_content)
# gpg_sig = message_native.read(gpg_msg.signature.data)
#
# release_data = apt_operations.release(info_url, gpg_msg.signed_message.text)
#
# if repo_src.signed_by:
#     gpg_key_result, gpg_key_content = client.get_raw(repo_src.signed_by)
#     gpg_key = message_armor_radix64.read(gpg_key_content)
# else:
#     gpg_key = None
#
# # apt_models.RepositoryRelease(
# #     release = release_data,
# #     signature=gpg_sig.signature,
# #     public_key=gpg_key,
# # )
#
# else:
# release_data = None
# gpg_key = None
# # found_url, landmark = find.detect_landmarks(client, repo_src)
#
# # TODO: get each item async and show any file content?
# # TODO: if exactly one dist is provided, build the url including it
#
# context = self.get_context_data(**kwargs)
# # context["repo_Src"] = repo_Src
# # context["dists"] = dists
# # context["comps"] = comps
# # context["archs"] = archs
# context["html_listing"] = html_listing
# context["directory"] = directory or "/"
# context["release_info"] = release_info
# context["release_data"] = release_data
# context["gpg_key"] = gpg_key
