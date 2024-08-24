import contextlib
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone
from functools import cache
from pathlib import Path

from modules._platform import get_config_file, get_config_path, get_cwd, get_platform, local_config, user_config
from modules.version_matcher import VersionSearchQuery
from PyQt5.QtCore import QSettings
from semver import Version

EPOCH = datetime.fromtimestamp(0, tz=timezone.utc)
ISO_EPOCH = EPOCH.isoformat()

# TODO: Simplify this

tabs = {
    "Library": 0,
    "Downloads": 1,
    "User": 2,
}

library_pages = {
    "Stable Releases": 0,
    "Daily Builds": 1,
    "Experimental Branches": 2,
}


downloads_pages = {
    "Stable Releases": 0,
    "Daily Builds": 1,
    "Experimental Branches": 2,
}


favorite_pages = {
    "Disable": 0,
    "Stable Releases": 1,
    "Daily Builds": 2,
    "Experimental Branches": 3,
}


library_subfolders = [
    "custom",
    "stable",
    "daily",
    "experimental",
    "template",
]


proxy_types = {
    "None": 0,
    "HTTP": 1,
    "HTTPS": 2,
    "SOCKS4": 3,
    "SOCKS5": 4,
}


blender_minimum_versions = {
    "4.0": 0,
    "3.6": 1,
    "3.5": 2,
    "3.4": 3,
    "3.3": 4,
    "3.2": 5,
    "3.1": 6,
    "3.0": 7,
    "2.90": 8,
    "2.80": 9,
    "2.79": 10,
    "None": 11,
}


def get_settings():
    file = get_config_file()
    if not file.parent.is_dir():
        file.parent.mkdir(parents=True)

    return QSettings(get_config_file().as_posix(), QSettings.Format.IniFormat)


def get_actual_library_folder():
    settings = get_settings()
    library_folder = settings.value("library_folder")

    if not is_library_folder_valid(library_folder):
        library_folder = get_cwd()
        settings.setValue("library_folder", library_folder)

    return Path(library_folder)


def get_library_folder():
    return get_actual_library_folder().resolve()


def is_library_folder_valid(library_folder=None):
    if library_folder is None:
        library_folder = get_settings().value("library_folder")

    if (library_folder is not None) and Path(library_folder).exists():
        try:
            (Path(library_folder) / ".temp").mkdir(parents=True, exist_ok=True)
        except PermissionError:
            return False

        return True

    return False


def set_library_folder(new_library_folder: str):
    settings = get_settings()

    if is_library_folder_valid(new_library_folder) is True:
        settings.setValue("library_folder", new_library_folder)
        create_library_folders(new_library_folder)
        return True

    return False


def create_library_folders(library_folder):
    for subfolder in library_subfolders:
        (Path(library_folder) / subfolder).mkdir(parents=True, exist_ok=True)


def get_favorite_path():
    return get_settings().value("Internal/favorite_path")


def set_favorite_path(path):
    get_settings().setValue("Internal/favorite_path", path)


def get_last_time_checked_utc():
    v = get_settings().value("Internal/last_time_checked_utc", defaultValue=ISO_EPOCH)
    return datetime.fromisoformat(v)


def set_last_time_checked_utc(dt: datetime):
    get_settings().setValue("Internal/last_time_checked_utc", dt.isoformat())


def get_launch_when_system_starts():
    if get_platform() == "Windows":
        import winreg

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run")
        path = sys.executable
        _, count, _ = winreg.QueryInfoKey(key)

        for i in range(count):
            with contextlib.suppress(OSError):
                name, value, _ = winreg.EnumValue(key, i)

                if name == "Blender Launcher":
                    return value == path

        key.Close()
    return False


def set_launch_when_system_starts(is_checked):
    if get_platform() == "Windows":
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )

        if is_checked:
            path = sys.executable
            winreg.SetValueEx(key, "Blender Launcher", 0, winreg.REG_SZ, path)
        else:
            with contextlib.suppress(Exception):
                winreg.DeleteValue(key, "Blender Launcher")

        key.Close()


def get_launch_minimized_to_tray():
    return get_settings().value("launch_minimized_to_tray", type=bool)


def set_launch_minimized_to_tray(is_checked):
    get_settings().setValue("launch_minimized_to_tray", is_checked)


def get_enable_high_dpi_scaling():
    return get_settings().value("enable_high_dpi_scaling", defaultValue=True, type=bool)


def set_enable_high_dpi_scaling(is_checked):
    get_settings().setValue("enable_high_dpi_scaling", is_checked)


def get_sync_library_and_downloads_pages():
    return get_settings().value("sync_library_and_downloads_pages", defaultValue=True, type=bool)


def set_sync_library_and_downloads_pages(is_checked):
    get_settings().setValue("sync_library_and_downloads_pages", is_checked)


def get_default_library_page():
    return get_settings().value("default_library_page", defaultValue=0, type=int)


def set_default_library_page(page):
    get_settings().setValue("default_library_page", library_pages[page])


def get_mark_as_favorite():
    return get_settings().value("mark_as_favorite", defaultValue=0, type=int)


def set_mark_as_favorite(page):
    get_settings().setValue("mark_as_favorite", favorite_pages[page])


def get_default_downloads_page():
    return get_settings().value("default_downloads_page", defaultValue=0, type=int)


def set_default_downloads_page(page):
    get_settings().setValue("default_downloads_page", downloads_pages[page])


def get_default_tab():
    return get_settings().value("default_tab", defaultValue=0, type=int)


def set_default_tab(tab):
    get_settings().setValue("default_tab", tabs[tab])


def get_list_sorting_type(list_name):
    return get_settings().value(f"Internal/{list_name}_sorting_type", defaultValue=1, type=int)


def set_list_sorting_type(list_name, sorting_type):
    get_settings().setValue(f"Internal/{list_name}_sorting_type", sorting_type.value)


def get_enable_new_builds_notifications():
    return get_settings().value("enable_new_builds_notifications", defaultValue=True, type=bool)


def set_enable_new_builds_notifications(is_checked):
    get_settings().setValue("enable_new_builds_notifications", is_checked)


def get_enable_download_notifications():
    return get_settings().value("enable_download_notifications", defaultValue=True, type=bool)


def set_enable_download_notifications(is_checked):
    get_settings().setValue("enable_download_notifications", is_checked)


def get_blender_startup_arguments() -> str:
    return get_settings().value("blender_startup_arguments", defaultValue="", type=str).strip()


def set_blender_startup_arguments(args):
    get_settings().setValue("blender_startup_arguments", args.strip())


def get_bash_arguments():
    return get_settings().value("bash_arguments", defaultValue="", type=str).strip()


def set_bash_arguments(args):
    get_settings().setValue("bash_arguments", args.strip())


def get_install_template():
    return get_settings().value("install_template", type=bool)


def set_install_template(is_checked):
    get_settings().setValue("install_template", is_checked)


def get_show_tray_icon():
    return get_settings().value("show_tray_icon", defaultValue=False, type=bool)


def set_show_tray_icon(is_checked):
    get_settings().setValue("show_tray_icon", is_checked)


def get_tray_icon_notified():
    return get_settings().value("Internal/tray_icon_notified", defaultValue=False, type=bool)


def set_tray_icon_notified(b=True):
    get_settings().setValue("Internal/tray_icon_notified", b)


def get_launch_blender_no_console():
    return get_settings().value("launch_blender_no_console", defaultValue=True, type=bool)


def set_launch_blender_no_console(is_checked):
    get_settings().setValue("launch_blender_no_console", is_checked)


def get_quick_launch_key_seq():
    return get_settings().value("quick_launch_key_seq", defaultValue="alt+f11", type=str).strip()


def set_quick_launch_key_seq(key_seq):
    get_settings().setValue("quick_launch_key_seq", key_seq.strip())


def get_enable_quick_launch_key_seq():
    return get_settings().value("enable_quick_launch_key_seq", defaultValue=False, type=bool)


def set_enable_quick_launch_key_seq(is_checked):
    get_settings().setValue("enable_quick_launch_key_seq", is_checked)


def get_proxy_type():
    return get_settings().value("proxy/type", defaultValue=0, type=int)


def set_proxy_type(proxy_type):
    get_settings().setValue("proxy/type", proxy_types[proxy_type])


def get_proxy_host():
    host = get_settings().value("proxy/host")

    if host is None:
        return "255.255.255.255"
    return host.strip()


def set_proxy_host(args):
    get_settings().setValue("proxy/host", args.strip())


def get_proxy_port():
    port = get_settings().value("proxy/port")

    if port is None:
        return "99999"
    return port.strip()


def set_proxy_port(args):
    get_settings().setValue("proxy/port", args.strip())


def get_proxy_user():
    user = get_settings().value("proxy/user")

    if user is None:
        return ""
    return user.strip()


def set_proxy_user(args):
    get_settings().setValue("proxy/user", args.strip())


def get_proxy_password():
    password = get_settings().value("proxy/password")

    if password is None:
        return ""
    return password.strip()


def set_proxy_password(args):
    get_settings().setValue("proxy/password", args.strip())


def get_use_custom_tls_certificates():
    return get_settings().value("use_custom_tls_certificates", defaultValue=True, type=bool)


def set_use_custom_tls_certificates(is_checked):
    get_settings().setValue("use_custom_tls_certificates", is_checked)


def get_user_id():
    user_id = get_settings().value("user_id", type=str).strip()
    if not user_id:
        user_id = str(uuid.uuid4())
        set_user_id(user_id)
    return user_id


def set_user_id(user_id):
    get_settings().setValue("user_id", user_id.strip())


# Blender Build Tab
def get_check_for_new_builds_automatically():
    settings = get_settings()

    if settings.contains("check_for_new_builds_automatically"):
        return settings.value("check_for_new_builds_automatically", type=bool)
    return False


def set_check_for_new_builds_automatically(is_checked):
    get_settings().setValue("check_for_new_builds_automatically", is_checked)


def get_new_builds_check_frequency():
    """Time in hours"""

    settings = get_settings()

    if settings.contains("new_builds_check_frequency"):
        return settings.value("new_builds_check_frequency", type=int)
    return 12


def set_new_builds_check_frequency(frequency):
    get_settings().setValue("new_builds_check_frequency", frequency)


def get_check_for_new_builds_on_startup():
    return get_settings().value("buildcheck_on_startup", defaultValue=True, type=bool)


def set_check_for_new_builds_on_startup(b: bool):
    get_settings().setValue("buildcheck_on_startup", b)


def get_minimum_blender_stable_version():
    value = get_settings().value("minimum_blender_stable_version")

    if value is not None and "." in value:
        return blender_minimum_versions.get(value, 7)

    return get_settings().value("minimum_blender_stable_version", defaultValue=7, type=int)


def set_minimum_blender_stable_version(blender_minimum_version):
    get_settings().setValue("minimum_blender_stable_version", blender_minimum_versions[blender_minimum_version])


def get_scrape_stable_builds() -> bool:
    return get_settings().value("scrape_stable_builds", defaultValue=True, type=bool)


def set_scrape_stable_builds(b: bool):
    get_settings().setValue("scrape_stable_builds", b)
    

def get_scrape_alternative_stable_builds() -> bool:
    return get_settings().value("scrape_alternative_stable_builds", defaultValue=False, type=bool)


def set_scrape_alternative_stable_builds(b: bool):
    get_settings().setValue("scrape_alternative_stable_builds", b)


def get_scrape_automated_builds() -> bool:
    return get_settings().value("scrape_automated_builds", defaultValue=True, type=bool)


def set_scrape_automated_builds(b: bool):
    get_settings().setValue("scrape_automated_builds", b)


def get_show_daily_archive_builds() -> bool:
    return get_settings().value("show_daily_archive_builds", defaultValue=False, type=bool)


def set_show_daily_archive_builds(b: bool):
    get_settings().setValue("show_daily_archive_builds", b)


def get_show_experimental_archive_builds() -> bool:
    return get_settings().value("show_experimental_archive_builds", defaultValue=False, type=bool)


def set_show_experimental_archive_builds(b: bool):
    get_settings().setValue("show_experimental_archive_builds", b)


def get_show_patch_archive_builds() -> bool:
    return get_settings().value("show_patch_archive_builds", defaultValue=False, type=bool)


def set_show_patch_archive_builds(b: bool):
    get_settings().setValue("show_patch_archive_builds", b)


def get_make_error_popup():
    return get_settings().value("error_popup", defaultValue=True, type=bool)


def set_make_error_notifications(v: bool):
    get_settings().setValue("error_popup", v)


def get_default_worker_thread_count() -> int:
    cpu_count = os.cpu_count()
    if cpu_count is None:  # why can os.cpu_count() return None
        return 4

    return round(max(cpu_count * 3 / 4, 1))


def get_worker_thread_count() -> int:
    v = get_settings().value("worker_thread_count", type=int)
    if v == 0:
        return get_default_worker_thread_count()

    return v


def set_worker_thread_count(v: int):
    get_settings().setValue("worker_thread_count", v)


def get_use_pre_release_builds():
    return get_settings().value("use_pre_release_builds", defaultValue=False, type=bool)


def set_use_pre_release_builds(b: bool):
    get_settings().setValue("use_pre_release_builds", b)


def get_use_system_titlebar():
    return get_settings().value("use_system_title_bar", defaultValue=False, type=bool)


def set_use_system_titlebar(b: bool):
    get_settings().setValue("use_system_title_bar", b)


def get_version_specific_queries() -> dict[Version, VersionSearchQuery]:
    import json

    dct = get_settings().value("version_specific_queries", defaultValue="{}", type=str)
    if dct is None:
        return {}
    return {Version.parse(k): VersionSearchQuery.parse(v) for k, v in json.loads(dct).items()}


def set_version_specific_queries(dct: dict[Version, VersionSearchQuery]):
    import json

    v = {str(k): str(v) for k, v in dct.items()}
    j = json.dumps(v)
    get_settings().setValue("version_specific_queries", j)


def get_launch_timer_duration() -> int:
    return get_settings().value("launch_timer", defaultValue=3, type=int)


def set_launch_timer_duration(duration: int):
    """Sets the launch timer duration, in seconds"""
    get_settings().setValue("launch_timer", duration)


def migrate_config(force=False):
    config_path = Path(get_config_path())
    old_config = local_config()
    new_config = user_config()
    if (old_config.is_file() and not new_config.is_file()) or force:
        if not config_path.is_dir():
            config_path.mkdir()
        shutil.move(old_config.resolve(), new_config.resolve())
