import datetime
import os
import sys
from pathlib import Path

from modules.build_info import BuildInfo, LaunchMode, LaunchOpenLast, LaunchWithBlendFile, get_args, parse_blender_ver
from semver import Version

from source.modules._platform import get_platform


def test_parser():
    args = [
        (("Blender1.0", True), Version(1, 0, 0)),
        (("blender-4.3.0-alpha-linux", True), Version(4, 3, 0, prerelease="alpha")),
        (("3.6.14", False), Version(3, 6, 14)),
        (("4.3.0-alpha+daily.ddc9f92777cd", True), Version(4, 3, 0, prerelease="alpha", build="daily.ddc9f92777cd")),
        (
            ("blender-3.3.21-stable+v33.e016c21db151-linux.x86_64-release.tar.xz", True),
            Version(3, 3, 21, prerelease="stable", build="v33.e016c21db151"),
        ),
        (("blender-4.1.0-linux-x64.tar.xz", False), Version(4, 1, 0)),
        (("2.80 (sub 75)", False), Version(2, 80, 0, prerelease="(sub 75)")),
        (("2.79rc1", False), Version(2, 79, 0, prerelease="rc1")),
    ]
    for (txt, search), ver in args:
        print(txt, search, ver)
        assert parse_blender_ver(txt, search) == ver
        if not search:  # things that do not need to be searched should also work when searched
            assert parse_blender_ver(txt, True) == ver


# TODO: Make all branches of this test, and get_args, OS-agnostic
def test_get_args():
    root = os.path.abspath(os.sep)
    info = BuildInfo(os.path.join(root, "blender"), "4.0.0", "ffffffff", datetime.datetime(2024, 12, 12), "daily")  # noqa: DTZ001
    info_c = BuildInfo(
        os.path.join(root, "blender"),
        "0.0.0",
        "",
        datetime.datetime(2024, 12, 12),  # noqa: DTZ001
        "daily",
        custom_executable="bforartists",
    )

    idx = ["Windows", "Linux", "macOS"].index(get_platform())

    x = [
        (
            get_args(info=info),
            ["C:\\blender\\blender.exe"],
            'nohup "/blender/blender" ',
            "open -W -n /blender/Blender/Blender.app --args",
        ),
        (
            get_args(info=info, linux_nohup=False),
            ["C:\\blender\\blender.exe"],
            ' "/blender/blender" ',
            "open -W -n /blender/Blender/Blender.app --args",
        ),
        (
            get_args(info=info, exe="bforartists.exe"),
            ["cmd", "/C", "C:\\blender\\bforartists.exe"],
            'nohup "/blender/blender" ',
            "open -W -n /blender/Blender/Blender.app --args",
        ),
        (
            get_args(info=info_c),
            ["C:\\blender\\bforartists"],
            'nohup "/blender/bforartists" ',
            "open -W -n /blender/Blender/Blender.app --args",
        ),
        (
            get_args(info=info, launch_mode=LaunchOpenLast()),
            ["C:\\blender\\blender.exe", "--open-last"],
            'nohup "/blender/blender"  --open-last',
            "open -W -n /blender/Blender/Blender.app --args --open-last",
        ),
        (
            get_args(info=info, launch_mode=LaunchWithBlendFile(Path(root) / "file.blend")),
            ["C:\\blender\\blender.exe", "/file.blend"],
            'nohup "/blender/blender"  "/file.blend"',
            'open -W -n /blender/Blender/Blender.app --args --open-last "/file.blend"',
        ),
    ]
    from pprint import pprint

    for i in x:
        pprint(i)
        assert i[0] == i[idx + 1]
