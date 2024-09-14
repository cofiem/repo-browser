import re

NAME_RELEASE_COMBINED = "InRelease"
NAME_RELEASE_DETACHED = "Release.gpg"
NAME_RELEASE_CLEAR = "Release"
NAME_DISTS = "dists"
NAME_BY_HASH = "by-hash"
NAME_POOL = "pool"
NAME_I18N = "i18n"
NAME_TOP_LISTING = "ls-lR.gz"
NAME_PACKAGES = "Packages"
NAME_CONTENTS = "Contents"

COMPONENTS_DIR_IGNORE = {
    i.casefold()
    for i in [
        NAME_RELEASE_COMBINED,
        NAME_RELEASE_DETACHED,
        NAME_RELEASE_CLEAR,
        NAME_BY_HASH,
        "changelog",
        NAME_POOL,
        f"{NAME_CONTENTS}-",
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
        NAME_BY_HASH,
        "-all",
        NAME_I18N,
        "dep11",
        "cnf",
        "uefi",
        "signed",
    ]
}
RE_LIST_ENTRY: re.Pattern[str] = re.compile(
    rf"^deb(-src)?\s*(\[(?P<extras>(\s*\S+\s*=\s*\S+\s*)*)])?\s*(?P<url>\S+)\s+(?P<dist>\S+)\s+(?P<comp>.+)$"
)
