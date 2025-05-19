import io
import tarfile

import pytest

from mcp_chart_scanner.extract import extract_chart


def test_extract_chart_rejects_outside_members(tmp_path):
    tar_path = tmp_path / "evil.tgz"
    with tarfile.open(tar_path, "w:gz") as tar:
        data = b"malicious"
        info = tarfile.TarInfo(name="../evil.txt")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()

    with pytest.raises(RuntimeError):
        extract_chart(tar_path, dest_dir)
