import http
import pathlib
import typing

from intrigue.apt import models as apt_models, constants as apt_constants

from intrigue.http_client import HttpClient


def get_links(client: HttpClient, url: str):
    status, html = client.get_text(url)
    if status != http.HTTPStatus.OK:
        return None

    try:
        return client.from_html(url, html)
    except ValueError:
        return None


def _filter(items: typing.Iterable[str], ignored: typing.Collection[str]):
    results = set()
    for item in items:
        norm_item = item.casefold()
        ignored = any(ignore in norm_item for ignore in ignored)
        if ignored:
            continue
        results.add(item)
    return results


def distributions(client: HttpClient, apt_src: apt_models.RepositorySourceEntry) -> list[str]:
    """Get the provided distributions or those available in the APT archive repository."""
    results = set()

    if apt_src.distributions:
        return sorted(apt_src.distributions)

    dists_url = client.build_url(apt_src.url, apt_constants.NAME_DISTS)
    dists_listing = get_links(client, dists_url)
    if not dists_listing:
        return sorted(results)

    items = _filter(dists_listing.links, apt_constants.DISTRIBUTIONS_DIR_IGNORE)
    results.update(items)

    return sorted(results)


def components(client: HttpClient, apt_src: apt_models.RepositorySourceEntry) -> list[str]:
    """Get the provided components or those available in the APT archive repository."""
    results = set()

    if apt_src.components:
        return sorted(apt_src.components)

    src_url = apt_src.url
    dists = distributions(client, apt_src)
    for dist in dists:
        comps_url = client.build_url(src_url, apt_constants.NAME_DISTS, dist)
        comps_listing = get_links(client, comps_url)
        if not comps_listing:
            continue

        items = _filter(comps_listing.links, apt_constants.COMPONENTS_DIR_IGNORE)
        results.update(items)

    return sorted(results)


def architectures(client: HttpClient, apt_src: apt_models.RepositorySourceEntry) -> typing.Iterable[str]:
    """Get the provided architectures or those available in the APT archive repository."""
    results = set()

    if apt_src.architectures:
        return sorted(apt_src.architectures)

    src_url = apt_src.url
    dists = distributions(client, apt_src)
    comps = components(client, apt_src)

    for dist in dists:
        for comp in comps:
            archs_url = client.build_url(src_url, apt_constants.NAME_DISTS, dist, comp)
            archs_listing = get_links(client, archs_url)
            if not archs_listing:
                continue

            items = _filter(archs_listing.links, apt_constants.ARCHITECTURES_DIR_IGNORE)
            results.update([pathlib.Path(item.rsplit("-", maxsplit=1)[-1]).stem for item in items])

    return sorted(results)


def release(client: HttpClient, apt_src: apt_models.RepositorySourceEntry, dist: str):
    dists = apt_constants.NAME_DISTS
    rel_combined = apt_constants.NAME_RELEASE_COMBINED
    url_combined = client.build_url(apt_src.url, dists, dist, rel_combined)
    status_combined, content_combined = client.get_raw(url_combined)
    if status_combined == http.HTTPStatus.OK and content_combined:
        return {
            apt_constants.NAME_RELEASE_COMBINED: {
                'url': url_combined,
                'content': content_combined,
            }
        }

    rel_detached = apt_constants.NAME_RELEASE_DETACHED
    url_detached = client.build_url(apt_src.url, dists, dist, rel_detached)
    status_detached, content_detached = client.get_raw(url_detached)

    rel_clear = apt_constants.NAME_RELEASE_CLEAR
    url_clear = client.build_url(apt_src.url, dists, dist, rel_clear)
    status_clear, content_clear = client.get_raw(url_clear)
    if ((status_detached == http.HTTPStatus.OK and content_detached) and
            (status_clear == http.HTTPStatus.OK and content_clear)):
        return {
            apt_constants.NAME_RELEASE_DETACHED: {
                'url': url_detached,
                'content': content_detached,
            },
            apt_constants.NAME_RELEASE_CLEAR: {
                'url': url_clear,
                'content': content_clear,
            }
        }

    return {}
