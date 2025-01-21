import sys

import pytest
from modules.shortcut import association_is_registered, register_windows_filetypes, unregister_windows_filetypes

from tests.config import SKIP_TESTS_THAT_MODIFY_CONFIG


@pytest.mark.skipif(
    sys.platform != "win32" or SKIP_TESTS_THAT_MODIFY_CONFIG,
    reason="Invalid outside of Windows or cfg changes were disabled",
)
class TestWinRegistering:
    was_registered = association_is_registered() if sys.platform == "win32" else False

    def test_registering_and_unregistering(self):
        if self.was_registered:
            unregister_windows_filetypes()
            assert not association_is_registered()
            register_windows_filetypes()
            assert association_is_registered()
        else:
            register_windows_filetypes()
            assert association_is_registered()
            unregister_windows_filetypes()
            assert not association_is_registered()
