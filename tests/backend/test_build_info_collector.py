import datetime
import os
import sys
from pathlib import Path

import pytest
from modules.build_info import BuildInfo, read_blender_version
from semver import Version

from tests.config import TESTED_BUILD


@pytest.mark.skipif(
    TESTED_BUILD is None or not os.path.exists(TESTED_BUILD),
    reason="valid tesing build is not provided",
)
def test_read_blender_version():
    assert TESTED_BUILD is not None
    pth = Path(TESTED_BUILD)
    read_blender_version(pth)
    # success if no exception


def test_build_priority():
    before_ny = datetime.datetime(2024, 12, 31, tzinfo=datetime.timezone.utc)
    after_ny = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)
    assert BuildInfo("", "1.0.0", "", before_ny, "") < BuildInfo("", "1.0.1", "", before_ny, "")
    assert BuildInfo("", "1.0.0", "", before_ny, "") < BuildInfo("", "1.0.0", "", after_ny, "")
    assert BuildInfo("", "1.0.0", "hash", before_ny, "") == BuildInfo("", "1.0.0", "hash", before_ny, "")
    assert BuildInfo("", "1.0.0", "hash", before_ny, "") != BuildInfo("", "1.0.0", "", before_ny, "")
    assert BuildInfo("", "1.0.0", None, before_ny, "") == BuildInfo("", "1.0.0", None, before_ny, "")
    assert BuildInfo("", "1.0.0-daily", None, before_ny, "") != BuildInfo("", "1.0.0", None, before_ny, "")


def test_build_displays():
    assert BuildInfo._display_version(Version(4, 4, 0)) == "4.4.0"  # noqa: SLF001
    assert BuildInfo._display_version(Version(4, 4, 0, prerelease="alpha")) == "4.4.0"  # noqa: SLF001
    assert BuildInfo._display_version(Version(2, 79, 75)) == "2.79"  # noqa: SLF001
    assert BuildInfo._display_version(Version(2, 79, 75, prerelease="a")) == "2.79a"  # noqa: SLF001
    assert BuildInfo._display_version(Version(2, 79, 0, prerelease="b")) == "2.79b"  # noqa: SLF001
    assert BuildInfo._display_version(Version(2, 83, 0, prerelease="alpha")) == "2.83alpha"  # noqa: SLF001
    # NGL the _display_label logic is kinda confusing
    assert BuildInfo._display_label("lts", Version(0, 0, 1), "") == "LTS"  # noqa: SLF001
    assert (
        BuildInfo._display_label("experimental", Version(4, 4, 0, prerelease="npr-prototypers"), "4.4.0-npr-prototype")  # noqa: SLF001
        == "Npr Prototypers"
    )
    assert BuildInfo._display_label("experimental", Version(4, 4, 0), "4.4.0-npr-prototype") == "Npr-Prototype"  # noqa: SLF001
    assert BuildInfo._display_label("daily", Version(2, 80, 0, prerelease="rc2"), "2.80.0-rc2") == "Rc2"  # noqa: SLF001
    assert BuildInfo._display_label("daily", Version(2, 80, 0), "2.80.0-rc2") == "Rc2"  # noqa: SLF001
    assert (
        BuildInfo._display_label("stable", Version(2, 80, 0, prerelease="rc2"), "2.80.0-rc2") == "Release Candidate 2"  # noqa: SLF001
    )
    # Build variant case -- this could possibly be removed
    p = sys.platform
    sys.platform = "darwin"
    assert BuildInfo._display_label("stable", Version(2, 80, 0, prerelease="intel"), "2.80.0-rc2") == "Stable - intel"  # noqa: SLF001
    sys.platform = p
