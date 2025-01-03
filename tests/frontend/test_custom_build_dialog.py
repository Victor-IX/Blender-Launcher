from modules.icons import Icons
from PySide6.QtWidgets import QApplication
from widgets.build_state_widget import BuildStateWidget


def test_build_state_widget(qapplication: QApplication):
    window = BuildStateWidget(Icons.get(), None)
    window.setCount(3)
    assert window.active_icon == window.countIcon and window.countIcon.text() == "3"
    window.setNewBuild()
    assert window.active_icon == window.newBuildIcon
    window.setDownload()
    assert window.active_icon == window.downloadIcon
