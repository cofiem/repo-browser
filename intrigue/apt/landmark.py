import enum

import attrs
from beartype import beartype

from intrigue.apt import constants, utils


@beartype
@enum.unique
class MatchType(enum.Enum):
    UNKNOWN = 0
    EXACT_FILE = 1
    EXACT_DIR = 2
    COMPRESSED_FILE = 3


@beartype
@attrs.frozen
class Landmark:
    base: str
    path: list[str]
    url: str
    match_type: MatchType


@beartype
def dists_dir(base: str):
    path = [constants.NAME_DISTS]
    return Landmark(
        base=base, path=path, url=_build(base, path), match_type=MatchType.EXACT_FILE
    )


@beartype
def top_listing_file(base: str):
    path = [constants.NAME_TOP_LISTING]
    return Landmark(
        base=base, path=path, url=_build(base, path), match_type=MatchType.EXACT_FILE
    )


@beartype
def pool_dir(base: str):
    path = [constants.NAME_POOL]
    return Landmark(
        base=base, path=path, url=_build(base, path), match_type=MatchType.EXACT_DIR
    )


@beartype
def release_combined_file(base: str, dist: str):
    path = [constants.NAME_DISTS, dist, constants.NAME_RELEASE_COMBINED]
    return Landmark(
        base=base, path=path, url=_build(base, path), match_type=MatchType.EXACT_FILE
    )


@beartype
def release_clear_file(base: str, dist: str):
    path = [constants.NAME_DISTS, dist, constants.NAME_RELEASE_CLEAR]
    return Landmark(
        base=base, path=path, url=_build(base, path), match_type=MatchType.EXACT_FILE
    )


@beartype
def release_detached_file(base: str, dist: str):
    path = [constants.NAME_DISTS, dist, constants.NAME_RELEASE_DETACHED]
    return Landmark(
        base=base, path=path, url=_build(base, path), match_type=MatchType.EXACT_FILE
    )


@beartype
def contents_arch_file(base: str, dist: str, arch: str):
    path = [constants.NAME_DISTS, dist, f"{constants.NAME_CONTENTS}-{arch}"]
    return Landmark(
        base=base,
        path=path,
        url=_build(base, path),
        match_type=MatchType.COMPRESSED_FILE,
    )


@beartype
def dist_by_hash_dir(base: str, dist: str):
    path = [constants.NAME_DISTS, dist, constants.NAME_BY_HASH]
    return Landmark(
        base=base, path=path, url=_build(base, path), match_type=MatchType.EXACT_DIR
    )


@beartype
def i18n_dir(base: str, dist: str, comp: str):
    path = [constants.NAME_DISTS, dist, comp, constants.NAME_I18N]
    return Landmark(
        base=base, path=path, url=_build(base, path), match_type=MatchType.EXACT_DIR
    )


@beartype
def arch_binary_by_hash_dir(base: str, dist: str, comp: str, arch: str):
    path = [
        constants.NAME_DISTS,
        dist,
        comp,
        f"binary-{arch}",
        constants.NAME_BY_HASH,
    ]
    return Landmark(
        base=base, path=path, url=_build(base, path), match_type=MatchType.EXACT_DIR
    )


@beartype
def arch_packages_file(base: str, dist: str, comp: str, arch: str):
    path = [
        constants.NAME_DISTS,
        dist,
        comp,
        f"binary-{arch}",
        constants.NAME_PACKAGES,
    ]
    return Landmark(
        base=base,
        path=path,
        url=_build(base, path),
        match_type=MatchType.COMPRESSED_FILE,
    )


@beartype
def arch_release_file(base: str, dist: str, comp: str, arch: str):
    path = [
        constants.NAME_DISTS,
        dist,
        comp,
        f"binary-{arch}",
        constants.NAME_RELEASE_CLEAR,
    ]
    return Landmark(
        base=base, path=path, url=_build(base, path), match_type=MatchType.EXACT_FILE
    )


@beartype
def _build(base: str, path: list[str]) -> str:
    parts = utils.from_url(base)
    url = utils.to_url(parts.scheme, parts.netloc, *parts.path, *path)
    return url
