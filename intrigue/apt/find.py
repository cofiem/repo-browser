import http
import pathlib
import typing

from beartype import beartype

from intrigue.apt import (
    models as apt_models,
    utils as apt_utils,
    landmark,
)

from intrigue import http_client
from intrigue.apt.landmark import KnownItem

# TODO: https://s3.amazonaws.com/repo.mongodb.org/

# dists = find.distributions(client, repo_src)
# comps = find.components(client, repo_src)
# archs = find.architectures(client, repo_src)
#
# releases = []
# for dist in dists:
#     releases.append(find.release(client, repo_src, dist))

# messages.info(request, request.META.get("REMOTE_ADDR"))

COMPONENTS_DIR_IGNORE = {
    i.casefold()
    for i in [
        KnownItem.RELEASE_COMBINED.value,
        KnownItem.RELEASE_DETACHED.value,
        KnownItem.RELEASE_CLEAR.value,
        KnownItem.BY_HASH.value,
        "changelog",
        KnownItem.POOL.value,
        f"{KnownItem.CONTENTS.value}-",
    ]
}
DISTRIBUTIONS_DIR_IGNORE = {
    i.casefold()
    for i in [
        "readme",
    ]
}
ARCHITECTURES_DIR_IGNORE = {
    i.casefold()
    for i in [
        "-udeb-",
        "installer",
        "source",
        KnownItem.BY_HASH.value,
        "-all",
        KnownItem.I18N.value,
        "dep11",
        "cnf",
        "uefi",
        "signed",
    ]
}



@beartype
def get_links(client: http_client.HttpClient, url: str):
    status, html = client.get_text(url)
    if status != http.HTTPStatus.OK:
        return None

    try:
        return client.from_html(url, html)
    except ValueError:
        return None


@beartype
def _filter(items: typing.Iterable[str], ignored: typing.Collection[str]):
    results = set()
    for item in items:
        norm_item = item.casefold()
        ignored = any(ignore in norm_item for ignore in ignored)
        if ignored:
            continue
        results.add(item)
    return results


@beartype
def distributions(
    client: http_client.HttpClient, repo_src: apt_models.RepositorySourceEntry
) -> list[str]:
    """Get the provided distributions or those available in the APT archive repository."""
    results = set()

    if repo_src.distributions:
        return sorted(repo_src.distributions)

    dists_parts = apt_utils.from_url(repo_src.url)
    dists_url = apt_utils.to_url(
        dists_parts.scheme,
        dists_parts.netloc,
        *dists_parts.path,
        KnownItem.DISTS.value,
    )
    dists_listing = get_links(client, dists_url)
    if not dists_listing:
        return sorted(results)

    items = _filter(dists_listing.links, DISTRIBUTIONS_DIR_IGNORE)
    results.update(items)

    return sorted(results)


@beartype
def components(
    client: http_client.HttpClient, repo_src: apt_models.RepositorySourceEntry
) -> list[str]:
    """Get the provided components or those available in the APT archive repository."""
    results = set()

    if repo_src.components:
        return sorted(repo_src.components)

    src_url = repo_src.url
    dists = distributions(client, repo_src)
    for dist in dists:
        comps_parts = apt_utils.from_url(src_url)
        comps_url = apt_utils.to_url(
            comps_parts.scheme,
            comps_parts.netloc,
            *comps_parts.path,
            KnownItem.DISTS.value,
            dist,
        )
        comps_listing = get_links(client, comps_url)
        if not comps_listing:
            continue

        items = _filter(comps_listing.links, COMPONENTS_DIR_IGNORE)
        results.update(items)

    return sorted(results)


@beartype
def architectures(
    client: http_client.HttpClient, repo_src: apt_models.RepositorySourceEntry
) -> typing.Iterable[str]:
    """Get the provided architectures or those available in the APT archive repository."""
    results = set()

    if repo_src.architectures:
        return sorted(repo_src.architectures)

    src_url = repo_src.url
    dists = distributions(client, repo_src)
    comps = components(client, repo_src)

    for dist in dists:
        for comp in comps:
            archs_parts = apt_utils.from_url(src_url)
            archs_url = apt_utils.to_url(
                archs_parts.scheme,
                archs_parts.netloc,
                *archs_parts.path,
                KnownItem.DISTS.value,
                dist,
                comp,
            )
            archs_listing = get_links(client, archs_url)
            if not archs_listing:
                continue

            items = _filter(archs_listing.links, ARCHITECTURES_DIR_IGNORE)
            results.update(
                [pathlib.Path(item.rsplit("-", maxsplit=1)[-1]).stem for item in items]
            )

    return sorted(results)


@beartype
def release(
    client: http_client.HttpClient, repo_src: apt_models.RepositorySourceEntry, dist: str
):
    dists = KnownItem.DISTS.value
    rel_combined = KnownItem.RELEASE_COMBINED.value

    combined_parts = apt_utils.from_url(repo_src.url)
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
            KnownItem.RELEASE_COMBINED.value: {
                "url": combined_url,
                "content": content_combined,
            }
        }

    rel_detached = KnownItem.RELEASE_DETACHED.value
    detached_parts = apt_utils.from_url(repo_src.url)
    detached_url = apt_utils.to_url(
        detached_parts.scheme,
        detached_parts.netloc,
        *detached_parts.path,
        dists,
        dist,
        rel_detached,
    )
    status_detached, content_detached = client.get_raw(detached_url)

    rel_clear = KnownItem.RELEASE_CLEAR.value
    clear_parts = apt_utils.from_url(repo_src.url)
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
            KnownItem.RELEASE_DETACHED.value: {
                "url": detached_url,
                "content": content_detached,
            },
            KnownItem.RELEASE_CLEAR.value: {
                "url": clear_url,
                "content": content_clear,
            },
        }

    return {}


@beartype
def detect_landmarks(
    client: http_client.HttpClient, repo_src: apt_models.RepositorySourceEntry
)-> tuple[str|None, landmark.Landmark|None]:
    """Try to discover where the url is in an apt repo,
    by detecting landmarks by looking at the file listing for the given url."""
    url = repo_src.url

    # build the landmarks using the repo src properties
    landmarks = [
        # base only checks
        landmark.dists_dir(url),
        landmark.top_listing_file(url),
        landmark.pool_dir(url),
    ]
    for dist in repo_src.distributions:
        # base and dist
        landmarks.extend(
            [
                landmark.release_combined_file(url, dist),
                landmark.release_clear_file(url, dist),
                landmark.release_detached_file(url, dist),
                landmark.dist_by_hash_dir(url, dist),
            ]
        )
        for comp in repo_src.components:
            # base, dist, comp
            landmarks.extend(
                [
                    landmark.i18n_dir(url, dist, comp),
                ]
            )
            for arch in repo_src.architectures:
                # base, dist, arch
                landmarks.extend(
                    [
                        landmark.contents_arch_file(url, dist, arch),
                    ]
                )
                # base, dist, comp, arch
                landmarks.extend(
                    [
                        landmark.arch_binary_by_hash_dir(url, dist, comp, arch),
                        landmark.arch_packages_file(url, dist, comp, arch),
                        landmark.arch_release_file(url, dist, comp, arch),
                    ]
                )

    # use the found urls from the html listing
    # and compare to the built landmarks
    listing = get_links(client, comps_url)
    for found_url in html_listing.urls:
        for landmark_item in landmarks:
            if landmark_item.match(found_url):
                return found_url, landmark_item
    return None, None
