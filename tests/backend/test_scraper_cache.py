import datetime

from modules.build_info import BuildInfo
from modules.scraper_cache import ScraperCache, StableFolder

STABLE_FOLDER_CACHE = {
    "assets": [
        [
            "https://download.blender.org/release/Blender4.3/blender-4.3.2-linux-x64.tar.xz",
            {
                "file_version": "1.3",
                "blinfo": [
                    {
                        "branch": "stable",
                        "subversion": "4.3.2",
                        "build_hash": None,
                        "commit_time": "2024-12-17T03:40:55-05:00",
                        "custom_name": "",
                        "is_favorite": False,
                        "custom_executable": None,
                    }
                ],
            },
        ]
    ],
    "modified_date": "2024-12-17T08:41:00",
}

SCRAPER_CACHE_DICT = {
    "folders": {
        "4.2.0": {"assets": [], "modified_date": "2024-12-17T09:02:00"},
        "4.3.0": STABLE_FOLDER_CACHE,
    }
}


def test_stable_folder_deserialize():
    assert StableFolder.from_dict(STABLE_FOLDER_CACHE) == StableFolder(
        assets=[
            BuildInfo(
                link="https://download.blender.org/release/Blender4.3/blender-4.3.2-linux-x64.tar.xz",
                subversion="4.3.2",
                build_hash=None,
                commit_time=datetime.datetime(
                    2024, 12, 17, 3, 40, 55, tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=68400))
                ),
                branch="stable",
                custom_name="",
                is_favorite=False,
                custom_executable=None,
            )
        ],
        modified_date=datetime.datetime(2024, 12, 17, 8, 41),  # noqa: DTZ001
    )


def test_scraper_cache_deserialize():
    from semver import Version

    assert ScraperCache.from_dict(SCRAPER_CACHE_DICT) == ScraperCache(
        folders={
            Version(major=4, minor=2, patch=0, prerelease=None, build=None): StableFolder(
                assets=[],
                modified_date=datetime.datetime(2024, 12, 17, 9, 2),  # noqa: DTZ001
            ),
            Version(major=4, minor=3, patch=0, prerelease=None, build=None): StableFolder(
                assets=[
                    BuildInfo(
                        link="https://download.blender.org/release/Blender4.3/blender-4.3.2-linux-x64.tar.xz",
                        subversion="4.3.2",
                        build_hash=None,
                        commit_time=datetime.datetime(
                            2024,
                            12,
                            17,
                            3,
                            40,
                            55,
                            tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=68400)),
                        ),
                        branch="stable",
                        custom_name="",
                        is_favorite=False,
                        custom_executable=None,
                    )
                ],
                modified_date=datetime.datetime(2024, 12, 17, 8, 41),  # noqa: DTZ001
            ),
        }
    )
