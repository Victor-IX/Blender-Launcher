import datetime
import tempfile
from pathlib import Path

import pytest
from modules.build_info import BuildInfo
from modules.icons import Icons
from PySide6.QtWidgets import QApplication
from widgets.build_state_widget import BuildStateWidget


def test_build_state_widget(qapplication: QApplication):
    with tempfile.TemporaryDirectory() as tmpdir:
        window = BuildStateWidget(Icons.get(), None)
        window.setCount(3)
        assert window.active_icon == window.countIcon and window.countIcon.text() == "3"
        window.setNewBuild()
        assert window.active_icon == window.newBuildIcon
        window.setDownload()
        assert window.active_icon == window.downloadIcon
