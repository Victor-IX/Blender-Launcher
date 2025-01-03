import datetime

from modules.version_matcher import BasicBuildInfo, BInfoMatcher, VersionSearchQuery
from semver import Version

utc = datetime.timezone.utc  # noqa: UP017

builds = (
    BasicBuildInfo(Version.parse("1.2.3"), "stable", "", datetime.datetime(2020, 5, 4, tzinfo=utc)),
    BasicBuildInfo(Version.parse("1.2.2"), "stable", "", datetime.datetime(2020, 4, 2, tzinfo=utc)),
    BasicBuildInfo(Version.parse("1.2.1"), "daily", "", datetime.datetime(2020, 3, 1, tzinfo=utc)),
    BasicBuildInfo(Version.parse("1.2.4"), "stable", "", datetime.datetime(2020, 6, 3, tzinfo=utc)),
    BasicBuildInfo(Version.parse("3.6.14"), "lts", "", datetime.datetime(2024, 7, 16, tzinfo=utc)),
    BasicBuildInfo(Version.parse("4.2.0"), "stable", "", datetime.datetime(2024, 7, 16, tzinfo=utc)),
    BasicBuildInfo(Version.parse("4.3.0"), "daily", "", datetime.datetime(2024, 7, 30, tzinfo=utc)),
    BasicBuildInfo(Version.parse("4.3.0"), "daily", "", datetime.datetime(2024, 7, 28, tzinfo=utc)),
    BasicBuildInfo(Version.parse("4.3.1"), "daily", "", datetime.datetime(2024, 7, 20, tzinfo=utc)),
)
matcher = BInfoMatcher(builds)


def test_binfo_matcher():
    # find the latest minor builds with any patch number
    results = matcher.match(VersionSearchQuery("^", "^", "*", commit_time="*"))
    print(results)
    assert results == (
        BasicBuildInfo(Version.parse("4.3.0"), "daily", "", datetime.datetime(2024, 7, 30, tzinfo=utc)),
        BasicBuildInfo(Version.parse("4.3.0"), "daily", "", datetime.datetime(2024, 7, 28, tzinfo=utc)),
        BasicBuildInfo(Version.parse("4.3.1"), "daily", "", datetime.datetime(2024, 7, 20, tzinfo=utc)),
    )

    # find any version with a patch of 14
    results = matcher.match(VersionSearchQuery("*", "*", 14))
    assert results == (BasicBuildInfo(Version.parse("3.6.14"), "lts", "", datetime.datetime(2024, 7, 16, tzinfo=utc)),)

    # find any version in the lts branch
    results = matcher.match(VersionSearchQuery("*", "*", "*", branch="lts"))
    assert results == (BasicBuildInfo(Version.parse("3.6.14"), "lts", "", datetime.datetime(2024, 7, 16, tzinfo=utc)),)

    # find the latest daily builds for the latest major release
    results = matcher.match(VersionSearchQuery("^", "*", "*", branch="daily", commit_time="^"))
    assert results == (BasicBuildInfo(Version.parse("4.3.0"), "daily", "", datetime.datetime(2024, 7, 30, tzinfo=utc)),)

    # find oldest major release with any minor and largest patch
    results = matcher.match(VersionSearchQuery("-", "*", "^"))
    assert results == (BasicBuildInfo(Version.parse("1.2.4"), "stable", "", datetime.datetime(2020, 6, 3, tzinfo=utc)),)

    print("test_binfo_matcher successful!")


def test_vsq_serialization():
    import json

    for query in (
        VersionSearchQuery("^", "^", "*"),
        VersionSearchQuery("*", "*", 14),
        VersionSearchQuery("*", "*", "*", branch="lts"),
        VersionSearchQuery("^", "*", "*", branch="daily", commit_time="^"),
        VersionSearchQuery("-", "*", "^"),
        VersionSearchQuery(4, 0, 0),
        VersionSearchQuery(4, "*", "*"),
        VersionSearchQuery("^", "^", "*", branch="stable", commit_time=datetime.datetime(2020, 5, 4, tzinfo=utc)),
    ):
        result_before_serialization = matcher.match(query)

        serialized_query = str(query)
        print(serialized_query)
        deserialized_query = VersionSearchQuery.parse(serialized_query)
        print(deserialized_query)

        result_after_serialization = matcher.match(deserialized_query)

        assert result_before_serialization == result_after_serialization

    print("test_vsq_serialization successful!")


def test_search_query_parser():
    # Test parsing of search query strings
    assert VersionSearchQuery.parse("1.2.3") == VersionSearchQuery(1, 2, 3)
    assert VersionSearchQuery.parse("^.*.-") == VersionSearchQuery("^", "*", "-")
    assert VersionSearchQuery.parse("*.*.*-daily") == VersionSearchQuery("*", "*", "*", branch="daily")
    assert VersionSearchQuery.parse("*.*.*+cb886aba06d5") == VersionSearchQuery(
        "*", "*", "*", build_hash="cb886aba06d5"
    )
    assert VersionSearchQuery.parse("*.*.*@2024-07-31T23:53:51+00:00") == VersionSearchQuery(
        "*", "*", "*", commit_time=datetime.datetime(2024, 7, 31, 23, 53, 51, tzinfo=utc)
    )
    assert VersionSearchQuery.parse("*.*.*@2024-07-31 23:53:51+00:00") == VersionSearchQuery(
        "*", "*", "*", commit_time=datetime.datetime(2024, 7, 31, 23, 53, 51, tzinfo=utc)
    )
    # Test parsing of search query strings that are not valid
    try:
        VersionSearchQuery.parse("abc")
        raise AssertionError("Expected ValueError to be raised")
    except ValueError:
        pass

    print("test_search_query_parser successful!")


test_binfo_matcher()
test_vsq_serialization()
test_search_query_parser()
