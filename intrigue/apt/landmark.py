import enum

import attrs
from beartype import beartype

from intrigue import utils
from intrigue.apt import utils as apt_utils


@beartype
@enum.unique
class MatchType(enum.Enum):
    UNKNOWN = 0
    EXACT = 1
    COMPRESSED_FILE = 2


@beartype
@enum.unique
class KnownItem(enum.Enum):
    UNKNOWN = ""
    RELEASE_COMBINED = "InRelease"
    RELEASE_DETACHED = "Release.gpg"
    RELEASE_CLEAR = "Release"
    DISTS = "dists"
    BY_HASH = "by-hash"
    POOL = "pool"
    I18N = "i18n"
    TOP_LISTING = "ls-lR.gz"
    PACKAGES = "Packages"
    CONTENTS = "Contents"


@beartype
@attrs.frozen
class Landmark:
    base: str
    path: list[str]
    url: str
    name: KnownItem
    match_type: MatchType

    def match(self, url: str) -> bool:
        landmark_parts = apt_utils.from_url(self.url)
        found_parts = apt_utils.from_url(url)
        if self.match_type == MatchType.EXACT:
            result = landmark_parts == found_parts
            return result
        if self.match_type == MatchType.COMPRESSED_FILE:
            for name in utils.archive_extensions(landmark_parts.path[-1]):
                # TODO
                new_landmark_parts = apt_utils.SimpleUrl()
                if new_landmark_parts == found_parts:
                    return True
        return False


@beartype
def dists_dir(base: str):
    path = [KnownItem.DISTS.value]
    return Landmark(
        base=base,
        path=path,
        url=apt_utils.build_url(base, path),
        name=KnownItem.DISTS,
        match_type=MatchType.EXACT,
    )


@beartype
def top_listing_file(base: str):
    path = [KnownItem.TOP_LISTING.value]
    return Landmark(
        base=base,
        path=path,
        url=apt_utils.build_url(base, path),
        name=KnownItem.TOP_LISTING,
        match_type=MatchType.EXACT,
    )


@beartype
def pool_dir(base: str):
    path = [KnownItem.POOL.value]
    return Landmark(
        base=base,
        path=path,
        url=apt_utils.build_url(base, path),
        name=KnownItem.POOL,
        match_type=MatchType.EXACT,
    )


@beartype
def release_combined_file(base: str, dist: str):
    path = [KnownItem.DISTS.value, dist, KnownItem.RELEASE_COMBINED.value]
    return Landmark(
        base=base,
        path=path,
        url=apt_utils.build_url(base, path),
        name=KnownItem.RELEASE_COMBINED,
        match_type=MatchType.EXACT,
    )


@beartype
def release_clear_file(base: str, dist: str):
    path = [KnownItem.DISTS.value, dist, KnownItem.RELEASE_CLEAR.value]
    return Landmark(
        base=base,
        path=path,
        url=apt_utils.build_url(base, path),
        name=KnownItem.RELEASE_CLEAR,
        match_type=MatchType.EXACT,
    )


@beartype
def release_detached_file(base: str, dist: str):
    path = [KnownItem.DISTS.value, dist, KnownItem.RELEASE_DETACHED.value]
    return Landmark(
        base=base,
        path=path,
        url=apt_utils.build_url(base, path),
        name=KnownItem.RELEASE_DETACHED,
        match_type=MatchType.EXACT,
    )


@beartype
def dist_by_hash_dir(base: str, dist: str):
    path = [KnownItem.DISTS.value, dist, KnownItem.BY_HASH.value]
    return Landmark(
        base=base,
        path=path,
        url=apt_utils.build_url(base, path),
        name=KnownItem.BY_HASH,
        match_type=MatchType.EXACT,
    )


@beartype
def i18n_dir(base: str, dist: str, comp: str):
    path = [KnownItem.DISTS.value, dist, comp, KnownItem.I18N.value]
    return Landmark(
        base=base,
        path=path,
        url=apt_utils.build_url(base, path),
        name=KnownItem.I18N,
        match_type=MatchType.EXACT,
    )


@beartype
def contents_arch_file(base: str, dist: str, arch: str):
    path = [KnownItem.DISTS.value, dist, f"{KnownItem.CONTENTS.value}-{arch}"]
    return Landmark(
        base=base,
        path=path,
        url=apt_utils.build_url(base, path),
        name=KnownItem.CONTENTS,
        match_type=MatchType.COMPRESSED_FILE,
    )


@beartype
def arch_binary_by_hash_dir(base: str, dist: str, comp: str, arch: str):
    path = [
        KnownItem.DISTS.value,
        dist,
        comp,
        f"binary-{arch}",
        KnownItem.BY_HASH.value,
    ]
    return Landmark(
        base=base,
        path=path,
        url=apt_utils.build_url(base, path),
        name=KnownItem.BY_HASH,
        match_type=MatchType.EXACT,
    )


@beartype
def arch_packages_file(base: str, dist: str, comp: str, arch: str):
    path = [
        KnownItem.DISTS.value,
        dist,
        comp,
        f"binary-{arch}",
        KnownItem.PACKAGES.value,
    ]
    return Landmark(
        base=base,
        path=path,
        url=apt_utils.build_url(base, path),
        name=KnownItem.PACKAGES,
        match_type=MatchType.COMPRESSED_FILE,
    )


@beartype
def arch_release_file(base: str, dist: str, comp: str, arch: str):
    path = [
        KnownItem.DISTS.value,
        dist,
        comp,
        f"binary-{arch}",
        KnownItem.RELEASE_CLEAR.value,
    ]
    return Landmark(
        base=base,
        path=path,
        url=apt_utils.build_url(base, path),
        name=KnownItem.RELEASE_CLEAR,
        match_type=MatchType.EXACT,
    )
