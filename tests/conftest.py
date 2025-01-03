import shutil

import pytest
from modules._platform import get_config_file

from tests.config import SKIP_TESTS_THAT_MODIFY_CONFIG

cfg = get_config_file()
cfg_bak = cfg.parent / "Blender Launcher.ini.bak"
cfg_existed = cfg.exists()


def pytest_sessionstart(session: pytest.Session):
    if not SKIP_TESTS_THAT_MODIFY_CONFIG:  # noqa: SIM102
        # move the dev's config to a different spot
        if cfg_existed:
            # print("MOVE ", cfg, "TO", cfg_bak)
            shutil.move(cfg, cfg_bak)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int | pytest.ExitCode):
    if not SKIP_TESTS_THAT_MODIFY_CONFIG:
        # move the dev's config back
        if cfg_existed:
            # print("MOVE ", cfg_bak, "TO", cfg)
            shutil.move(cfg_bak, cfg)
        elif cfg.exists():  # the cfg was made by tests and should be deleted
            cfg.unlink()


@pytest.fixture(scope="session", autouse=True)
def qapplication():
    from PySide6.QtWidgets import QApplication

    app = QApplication(["blender-launcher-v2"])
    yield app
