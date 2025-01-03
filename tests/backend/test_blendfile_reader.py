import tempfile
from pathlib import Path

from modules.blendfile_reader import (
    BlendfileHeader,
    CompressionType,
    parse_header_version,
    read_blendfile_header,
)
from semver import Version

# This is innacurate to a normal scenario but they should scale properly
BASIC = b"BLENDER-v404"
GZIP = b"\x1f\x8b\x08\x00]nwg\x02\xffs\xf2q\xf5sq\r\xd2-310\x01\x00\x93\xd4+E\x0c\x00\x00\x00"
ZSTD = b"(\xb5/\xfd \x0ca\x00\x00BLENDER-v404"


def test_header_parser():
    assert parse_header_version(BASIC) == Version(4, 4, 0)
    with tempfile.TemporaryDirectory() as tmpdir_:
        tmpdir = Path(tmpdir_)
        gb = tmpdir / "gzip.blend"
        zb = tmpdir / "zstd.blend"
        with gb.open("wb") as g, zb.open("wb") as z:
            g.write(GZIP)
            z.write(ZSTD)

        assert read_blendfile_header(gb) == BlendfileHeader(Version(4, 4, 0), CompressionType.GZIP)
        assert read_blendfile_header(zb) == BlendfileHeader(Version(4, 4, 0), CompressionType.ZSTD)
