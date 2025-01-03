from __future__ import annotations

import contextlib
import datetime
import re
from dataclasses import dataclass
from functools import cache
from operator import attrgetter
from typing import TYPE_CHECKING

from semver import Version

if TYPE_CHECKING:
    from collections.abc import Sequence

    from modules.build_info import BuildInfo

utc = datetime.timezone.utc


@dataclass
class BasicBuildInfo:
    version: Version
    branch: str
    build_hash: str
    commit_time: datetime.datetime

    @property
    def major(self):
        return self.version.major

    @property
    def minor(self):
        return self.version.minor

    @property
    def patch(self):
        return self.version.patch

    def __lt__(self, other: BasicBuildInfo):
        if self.version == other.version:
            return self.commit_time < other.commit_time

        return self.version < other.version

    @classmethod
    def from_buildinfo(cls, buildinfo: BuildInfo):
        return BasicBuildInfo(
            version=buildinfo.full_semversion,
            branch=buildinfo.branch,
            build_hash=buildinfo.build_hash if buildinfo.build_hash is not None else "",
            commit_time=buildinfo.commit_time.astimezone(utc),
        )


# VersionSearchQuerySyntax (NOT SEMVER COMPATIBLE!):

# ^   | match the largest/newest item in that column
# *   | match any number in that column
# -   | match the smallest/oldest item in that column
# <n> | match an item in that column

VERSION_SEARCH_SYNTAX = "<major_num>.<minor>.<patch>[-<branch>][+<build_hash>][@<commit time>]"

# Valid examples of version search queries are:
# *.*.*
# 1.2.3-master
# 4.^.^-stable@^
# 4.3.^+cb886aba06d5@^
# 4.3.^@2024-07-31T23:53:51+00:00
# And of course, a full example:
# 4.3.^-stable+cb886aba06d5@2024-07-31T23:53:51+00:00

VERSION_SEARCH_REGEX = re.compile(
    r"""^
    ([\^\-\*]|\d+)\.([\^\-\*]|\d+)\.([\^\-\*]|\d+)
    (?:\-([^\@\s\+]+))?
    (?:\+([\d\w]+))?
    (?:\@([\^\-\*]|[\dT\+\:Z\ \^\-]+))?
    $""",
    flags=re.X,
)

# Regex breakdown:
# ^                                     -- start of string
# ([\^\-\*]|\d+)                     x3 -- major, minor, and patch (required)
# (?:\-([^\@\s\+]+))?                   -- branch (optional)
# (?:\+([\d\w]+))?                      -- build hash (optional)
# (?:\@([\dT\+\:Z\ \^\*\-]+))?            -- commit time (saved as ^|*|- or an isoformat) (optional)
# $                                     -- end of string


VALID_QUERIES = """^.^.*
*.*.14
*.*.*
^.*.*
-.*.^
4.2.^
4.^.^"""
VALID_FULL_QUERIES = """*.*.*
1.2.3-master
4.^,^-stable@^
4.3.^+cb886aba06d5@^
4.3.^@2024-07-31T23:53:51+00:00
4.3.^-stable+cb886aba06d5@2024-07-31T23:53:51+00:00
"""


@cache
def _parse(s: str) -> tuple[int | str, int | str, int | str, str | None, str | None, datetime.datetime | str]:
    """Parse a query from a string. does not support branch and commit_time"""
    match = VERSION_SEARCH_REGEX.match(s)
    if not match:
        raise ValueError(f"Invalid version search query: {s}")

    major = match.group(1)
    minor = match.group(2)
    patch = match.group(3)
    branch = match.group(4)
    build_hash = match.group(5)
    commit_time = match.group(6)
    if commit_time is None:
        commit_time = "^"

    if major.isnumeric():
        major = int(major)
    if minor.isnumeric():
        minor = int(minor)
    if patch.isnumeric():
        patch = int(patch)

    if commit_time is not None and commit_time not in ("^", "*", "-"):
        # Try to convert it to a datetime, and just passing it upon failure
        with contextlib.suppress(ValueError):
            commit_time = datetime.datetime.fromisoformat(commit_time)

    return major, minor, patch, branch, build_hash, commit_time


@dataclass
class VersionSearchQuery:
    """A dataclass for a search query. The attributes are ordered by priority"""

    major: int | str
    "A major release of Blender"

    minor: int | str
    "A minor release of Blender"

    patch: int | str
    "A patch release of Blender"

    branch: str | None = None
    "Which branch of Blender this is (stable, daily, experimental, etc.)"

    build_hash: str | None = None
    "The git hash of the build that this is"

    commit_time: datetime.datetime | str = "^"
    "When the build was made (in UTC)"

    def __post_init__(self):
        for pos in (self.major, self.minor, self.patch, self.commit_time):
            if isinstance(pos, str) and pos not in ["^", "*", "-"]:
                raise ValueError(f'{pos} must be in ["^", "*", "-"]')
        if self.build_hash and self.build_hash in ["^", "-"]:
            raise ValueError("build_hash cannot be temporally matched")
        if self.branch and self.branch in ["^", "-"]:
            raise ValueError("branch cannot be temporally matched")

    @classmethod
    def parse(cls, s: str):
        """Parse a query from a string. does not support branch and commit_time"""

        return cls(*_parse(s))

    @classmethod
    def default(cls):
        return cls("^", "^", "^", commit_time="^", branch=None)

    def __str__(self) -> str:
        """Returns a string that can be parsed by parse()"""
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.branch:
            s += f"-{self.branch}"
        if self.build_hash:
            s += f"+{self.build_hash}"
        if self.commit_time:
            s += f"@{self.commit_time}"
        return s

    def with_branch(self, branch: str | None = None):
        return self.__class__(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            branch=branch,
            build_hash=self.build_hash,
            commit_time=self.commit_time,
        )

    def with_build_hash(self, build_hash: str | None = None):
        return self.__class__(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            branch=self.branch,
            build_hash=build_hash,
            commit_time=self.commit_time,
        )

    def with_commit_time(self, commit_time: datetime.datetime | str):
        return self.__class__(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            branch=self.branch,
            build_hash=self.build_hash,
            commit_time=commit_time,
        )


# Examples:
# VersionSearchQuery("^", "^", "^"): Match the latest version(s)
# VersionSearchQuery(4, "^", "^"): Match the latest version of major 4
# VersionSearchQuery("^", "*", "*"): Match any version in the latest major release


@dataclass
class BInfoMatcher:
    versions: tuple[BasicBuildInfo, ...]

    def match(self, s: VersionSearchQuery) -> tuple[BasicBuildInfo, ...]:
        versions = self.versions

        for place in ("build_hash", "major", "minor", "patch", "branch", "commit_time"):
            getter = attrgetter(place)
            p: str | int | datetime.datetime | None = getter(s)
            if p == "^":
                # get the max number for `place` in version
                max_p = max(getter(v) for v in versions)

                versions = [v for v in versions if getter(v) == max_p]
            elif p == "*" or p is None:
                continue  # all versions match
            elif p == "-":
                # get the min number for `place` in version
                min_p = min(getter(v) for v in versions)

                versions = [v for v in versions if getter(v) == min_p]
            else:
                versions = [v for v in versions if getter(v) == p]

            if not versions:
                return ()

        return tuple(versions)
