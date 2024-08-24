from __future__ import annotations

import contextlib
import json
import logging
import re
from datetime import datetime, timezone
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urljoin

import distro
from bs4 import BeautifulSoup, SoupStrainer
from modules._platform import get_architecture, get_platform, reset_locale, set_locale, stable_cache_path
from modules.build_info import BuildInfo, parse_blender_ver
from modules.scraper_cache import StableCache
from modules.settings import (
    blender_minimum_versions,
    get_minimum_blender_stable_version,
    get_scrape_automated_builds,
    get_scrape_stable_builds,
    get_scrape_alternative_stable_builds,
    get_show_daily_archive_builds,
    get_show_experimental_archive_builds,
    get_show_patch_archive_builds,
    get_use_pre_release_builds,
)
from PyQt5.QtCore import QThread, pyqtSignal
from semver import Version

if TYPE_CHECKING:
    from modules.connection_manager import ConnectionManager

logger = logging.getLogger()


def get_latest_tag(
    connection_manager: ConnectionManager,
    url,
) -> str | None:
    r = connection_manager.request("GET", url)

    if r is None:
        return None

    url = r.geturl()
    tag = url.rsplit("/", 1)[-1]

    r.release_conn()
    r.close()

    return tag


def get_latest_pre_release_tag(
    connection_manager: ConnectionManager,
    url,
) -> str | None:
    r = connection_manager.request("GET", url)

    if r is None:
        return None

    try:
        parsed_data = json.loads(r.data)
    except json.JSONDecodeError:
        return None

    platform = get_platform()

    if platform.lower() == "linux":
        for key in (
            distro.id().title(),
            distro.like().title(),
            distro.id(),
            distro.like(),
        ):
            if "ubuntu" in key.lower():
                platform = "Ubuntu"
                break

    platform_valid_tags = (
        release["tag_name"]
        for release in parsed_data
        for asset in release["assets"]
        if asset["name"].endswith(".zip") and platform.lower() in asset["name"].lower()
    )
    pre_release_tags = (release.lstrip("v") for release in platform_valid_tags)

    valid_pre_release_tags = [tag for tag in pre_release_tags if Version.is_valid(tag)]

    if valid_pre_release_tags:
        tag = max(valid_pre_release_tags, key=Version.parse)
        return f"v{tag}"

    r.release_conn()
    r.close()

    return None


class Scraper(QThread):
    links = pyqtSignal(BuildInfo)
    new_bl_version = pyqtSignal(str)
    error = pyqtSignal()
    stable_error = pyqtSignal(str)

    def __init__(self, parent, man: ConnectionManager):
        QThread.__init__(self)
        self.parent = parent
        self.manager = man
        self.platform = get_platform()
        self.architecture = get_architecture()

        self.cache_path = stable_cache_path()

        if self.cache_path.exists():
            with stable_cache_path().open("r", encoding="utf-8") as f:
                cache = json.load(f)
                self.cache = StableCache.from_dict(cache)
                logging.debug(f"Loaded cache from {self.cache_path!r}")
        else:
            self.cache = StableCache()

        self.json_platform = {
            "Windows": "windows",
            "Linux": "linux",
            "macOS": "darwin",
        }.get(self.platform, self.platform)

        if self.platform == "Windows":
            regex_filter = r"blender-.+win.+64.+zip$"
        elif self.platform == "macOS":
            regex_filter = r"blender-.+(macOS|darwin).+dmg$"
        else:
            regex_filter = r"blender-.+lin.+64.+tar+(?!.*sha256).*"

        self.b3d_link = re.compile(regex_filter, re.IGNORECASE)
        self.hash = re.compile(r"\w{12}")
        self.subversion = re.compile(r"-\d\.[a-zA-Z0-9.]+-")

        self.scrape_stable = get_scrape_stable_builds()
        self.scrape_automated = get_scrape_automated_builds()

    def run(self):
        self.get_download_links()

        assert self.manager.manager is not None
        if get_use_pre_release_builds():
            url = "https://api.github.com/repos/Victor-IX/Blender-Launcher-V2/releases"
            latest_tag = get_latest_pre_release_tag(self.manager, url)
        else:
            url = "https://github.com/Victor-IX/Blender-Launcher-V2/releases/latest"
            latest_tag = get_latest_tag(self.manager, url)

        if latest_tag is not None:
            self.new_bl_version.emit(latest_tag)
        self.manager.manager.clear()

    def get_download_links(self):
        set_locale()

        scrapers = []
        if self.scrape_stable:
            scrapers.append(self.scrap_stable_releases())
        if self.scrape_automated:
            scrapers.append(self.scrape_automated_releases())
        for build in chain(*scrapers):
            self.links.emit(build)

        reset_locale()

    def scrape_automated_releases(self):
        base_fmt = "https://builder.blender.org/download/{}/?format=json&v=1"

        branch_mapping = {
            "daily": get_show_daily_archive_builds,
            "experimental": get_show_experimental_archive_builds,
            "patch": get_show_patch_archive_builds,
        }

        branches = tuple(
            f"{branch}/archive" if check_archive() else branch for branch, check_archive in branch_mapping.items()
        )

        for branch_type in branches:
            url = base_fmt.format(branch_type)
            r = self.manager.request("GET", url)

            if r is None:
                continue

            data = json.loads(r.data)
            architecture_specific_build = False

            # Remove /archive from branch name
            if "/archive" in branch_type:
                branch_type = branch_type.replace("/archive", "")

            for build in data:
                if (
                    build["platform"] == self.json_platform
                    and build["architecture"].lower() == self.architecture.lower()
                    and self.b3d_link.match(build["file_name"])
                ):
                    architecture_specific_build = True
                    yield self.new_build_from_dict(build, branch_type, architecture_specific_build)

            if not architecture_specific_build:
                logger.warning(
                    f"No builds found for {branch_type} build on {self.platform} architecture {self.architecture}"
                )

                for build in data:
                    if build["platform"] == self.json_platform and self.b3d_link.match(build["file_name"]):
                        yield self.new_build_from_dict(build, branch_type, architecture_specific_build)

    def new_build_from_dict(self, build, branch_type, architecture_specific_build):
        dt = datetime.fromtimestamp(build["file_mtime"], tz=timezone.utc)

        subversion = parse_blender_ver(build["version"])
        build_var = ""
        if build["patch"] is not None and branch_type != "daily":
            build_var = build["patch"]
        if build["release_cycle"] is not None and branch_type == "daily":
            build_var = build["release_cycle"]
        if build["branch"] and branch_type == "experimental":
            build_var = build["branch"]

        if "architecture" in build and not architecture_specific_build:
            if build["architecture"] == "amd64":
                build["architecture"] = "x86_64"
            build_var += " | " + build["architecture"]

        if build_var:
            subversion = subversion.replace(prerelease=build_var)

        return BuildInfo(
            build["url"],
            str(subversion),
            build["hash"],
            dt,
            branch_type,
        )

    def scrap_download_links(self, url, branch_type, _limit=None):
        r = self.manager.request("GET", url)

        if r is None:
            return

        content = r.data

        soup_stainer = SoupStrainer("a", href=True)
        soup = BeautifulSoup(content, "lxml", parse_only=soup_stainer)

        for tag in soup.find_all(limit=_limit, href=self.b3d_link):
            build_info = self.new_blender_build(tag, url, branch_type)

            if build_info is not None:
                yield build_info

        r.release_conn()
        r.close()

    def new_blender_build(self, tag, url, branch_type):
        link = urljoin(url, tag["href"]).rstrip("/")
        r = self.manager.request("HEAD", link)

        if r is None:
            return None

        if r.status != 200:
            return None

        info = r.headers
        build_hash: str | None = None
        stem = Path(link).stem
        match = re.findall(self.hash, stem)

        if match:
            build_hash = match[-1].replace("-", "")

        subversion = parse_blender_ver(stem, search=True)
        branch = branch_type
        if branch_type != "stable":
            build_var = ""
            tag = tag.find_next("span", class_="build-var")

            # For some reason tag can be None on macOS
            if tag is not None:
                build_var = tag.get_text()

            if self.platform == "macOS":
                if "arm64" in link:
                    build_var = "{} │ {}".format(build_var, "Arm")
                elif "x86_64" in link:
                    build_var = "{} │ {}".format(build_var, "Intel")

            if branch_type == "experimental":
                branch = build_var
            elif branch_type == "daily":
                branch = "daily"
                subversion = subversion.replace(prerelease=build_var)

        commit_time = datetime.strptime(info["last-modified"], "%a, %d %b %Y %H:%M:%S %Z").astimezone()

        r.release_conn()
        r.close()
        return BuildInfo(link, str(subversion), build_hash, commit_time, branch)

    def scrap_stable_releases(self):
        if get_scrape_alternative_stable_builds():
            url = "https://www.blender.org/download/"
        else:
            url = "https://download.blender.org/release/"
        
        
        print (url) 
        
        r = self.manager.request("GET", url)

        if r is None:
            return

        content = r.data
        soup = BeautifulSoup(content, "lxml")

        b3d_link = re.compile(r"Blender(\d+\.\d+)")

        releases = soup.find_all(href=b3d_link)
        if not any(releases):
            logger.info("Failed to gather stable releases")
            logger.info(content)
            self.stable_error.emit(
                "No releases were scraped from the site!<br>check -debug logs for more details."
            )
            return

        # Convert string to Verison
        minimum_version_index = get_minimum_blender_stable_version()
        version_at_index = list(blender_minimum_versions.keys())[minimum_version_index]
        if version_at_index == "None":
            minimum_smver_version = Version(0, 0, 0)
        else:
            major, minor = version_at_index.split(".")
            minimum_smver_version = Version(int(major), int(minor), 0)

        cache_modified = False
        for release in releases:
            href = release["href"]
            match = re.search(b3d_link, href)
            if match is None:
                continue

            ver = parse_blender_ver(match.group(1))
            if ver >= minimum_smver_version:
                # Check modified dates of folders, if available
                date_sibling = release.find_next_sibling(string=True)
                if date_sibling:
                    date_str = " ".join(date_sibling.strip().split()[:2])
                    with contextlib.suppress(ValueError):
                        modified_date = datetime.strptime(date_str, "%d-%b-%Y %H:%M").astimezone(tz=timezone.utc)
                        if ver not in self.cache:
                            logger.debug(f"Creating new folder for version {ver}")
                            folder = self.cache.new_build(ver)
                        else:
                            folder = self.cache[ver]

                        if folder.modified_date != modified_date:
                            builds = list(self.scrap_download_links(urljoin(url, href), "stable"))
                            logger.debug(f"Caching {href}: {modified_date} (previous was {folder.modified_date})")

                            folder.assets = builds
                            folder.modified_date = modified_date

                            cache_modified = True
                        else:
                            logger.debug(f"Skipping {href}: {modified_date}")
                        builds = self.cache[ver].assets
                        yield from builds
                        continue

                yield from self.scrap_download_links(urljoin(url, href), "stable")

        if cache_modified:
            with self.cache_path.open("w", encoding="utf-8") as f:
                json.dump(self.cache.to_dict(), f)
                logging.debug(f"Saved cache to {self.cache_path}")

        r.release_conn()
        r.close()
