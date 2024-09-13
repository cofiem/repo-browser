import http
import pathlib
import typing

from intrigue.apt import (
    models as apt_models,
    constants as apt_constants,
    utils as apt_utils,
)

from intrigue.http_client import HttpClient

# TODO: https://s3.amazonaws.com/repo.mongodb.org/

# dists = find.distributions(client, apt_src)
# comps = find.components(client, apt_src)
# archs = find.architectures(client, apt_src)
#
# releases = []
# for dist in dists:
#     releases.append(find.release(client, apt_src, dist))

# messages.info(request, request.META.get("REMOTE_ADDR"))


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


def distributions(
    client: HttpClient, apt_src: apt_models.RepositorySourceEntry
) -> list[str]:
    """Get the provided distributions or those available in the APT archive repository."""
    results = set()

    if apt_src.distributions:
        return sorted(apt_src.distributions)

    dists_parts = apt_utils.from_url(apt_src.url)
    dists_url = apt_utils.to_url(
        dists_parts.scheme,
        dists_parts.netloc,
        *dists_parts.path,
        apt_constants.NAME_DISTS,
    )
    dists_listing = get_links(client, dists_url)
    if not dists_listing:
        return sorted(results)

    items = _filter(dists_listing.links, apt_constants.DISTRIBUTIONS_DIR_IGNORE)
    results.update(items)

    return sorted(results)


def components(
    client: HttpClient, apt_src: apt_models.RepositorySourceEntry
) -> list[str]:
    """Get the provided components or those available in the APT archive repository."""
    results = set()

    if apt_src.components:
        return sorted(apt_src.components)

    src_url = apt_src.url
    dists = distributions(client, apt_src)
    for dist in dists:
        comps_parts = apt_utils.from_url(src_url)
        comps_url = apt_utils.to_url(
            comps_parts.scheme,
            comps_parts.netloc,
            *comps_parts.path,
            apt_constants.NAME_DISTS,
            dist,
        )
        comps_listing = get_links(client, comps_url)
        if not comps_listing:
            continue

        items = _filter(comps_listing.links, apt_constants.COMPONENTS_DIR_IGNORE)
        results.update(items)

    return sorted(results)


def architectures(
    client: HttpClient, apt_src: apt_models.RepositorySourceEntry
) -> typing.Iterable[str]:
    """Get the provided architectures or those available in the APT archive repository."""
    results = set()

    if apt_src.architectures:
        return sorted(apt_src.architectures)

    src_url = apt_src.url
    dists = distributions(client, apt_src)
    comps = components(client, apt_src)

    for dist in dists:
        for comp in comps:
            archs_parts = apt_utils.from_url(src_url)
            archs_url = apt_utils.to_url(
                archs_parts.scheme,
                archs_parts.netloc,
                *archs_parts.path,
                apt_constants.NAME_DISTS,
                dist,
                comp,
            )
            archs_listing = get_links(client, archs_url)
            if not archs_listing:
                continue

            items = _filter(archs_listing.links, apt_constants.ARCHITECTURES_DIR_IGNORE)
            results.update(
                [pathlib.Path(item.rsplit("-", maxsplit=1)[-1]).stem for item in items]
            )

    return sorted(results)


def release(client: HttpClient, apt_src: apt_models.RepositorySourceEntry, dist: str):
    dists = apt_constants.NAME_DISTS
    rel_combined = apt_constants.NAME_RELEASE_COMBINED

    combined_parts = apt_utils.from_url(apt_src.url)
    combined_url = apt_utils.to_url(
        combined_parts.scheme,
        combined_parts.netloc,
        *combined_parts.path,
        dists,
        dist,
        rel_combined,
    )
    status_combined, content_combined = client.get_raw(combined_url)
    if status_combined == http.HTTPStatus.OK and content_combined:
        return {
            apt_constants.NAME_RELEASE_COMBINED: {
                "url": combined_url,
                "content": content_combined,
            }
        }

    rel_detached = apt_constants.NAME_RELEASE_DETACHED
    detached_parts = apt_utils.from_url(apt_src.url)
    detached_url = apt_utils.to_url(
        detached_parts.scheme,
        detached_parts.netloc,
        *detached_parts.path,
        dists,
        dist,
        rel_detached,
    )
    status_detached, content_detached = client.get_raw(detached_url)

    rel_clear = apt_constants.NAME_RELEASE_CLEAR
    clear_parts = apt_utils.from_url(apt_src.url)
    clear_url = apt_utils.to_url(
        clear_parts.scheme,
        clear_parts.netloc,
        *clear_parts.path,
        dists,
        dist,
        rel_clear,
    )
    status_clear, content_clear = client.get_raw(clear_url)
    if (status_detached == http.HTTPStatus.OK and content_detached) and (
        status_clear == http.HTTPStatus.OK and content_clear
    ):
        return {
            apt_constants.NAME_RELEASE_DETACHED: {
                "url": detached_url,
                "content": content_detached,
            },
            apt_constants.NAME_RELEASE_CLEAR: {
                "url": clear_url,
                "content": content_clear,
            },
        }

    return {}
