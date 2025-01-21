import uuid

import pytest
from modules.settings import (
    get_default_worker_thread_count,
    get_user_id,
    get_version_specific_queries,
    set_version_specific_queries,
)
from modules.version_matcher import VersionSearchQuery
from semver import Version

from tests.config import SKIP_TESTS_THAT_MODIFY_CONFIG


@pytest.mark.skipif(SKIP_TESTS_THAT_MODIFY_CONFIG, reason="Tests that modify the config is disabled")
class TestConfig:
    def test_saving_vsq(self):
        version_specific_queries = {
            Version(4, 2, 0): VersionSearchQuery(4, "^", "^", branch="daily"),
            Version(2, 80, 0): VersionSearchQuery(2, "^", "^", commit_time="^"),
        }

        set_version_specific_queries(version_specific_queries)
        assert get_version_specific_queries() == version_specific_queries
