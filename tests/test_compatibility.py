"""Tests for marketplace compatibility functionality."""

from unittest import mock

from mcp_chart_scanner.server.mcp_server import check_marketplace_compatibility


@mock.patch("mcp_chart_scanner.server.mcp_server.check_helm_cli")
def test_check_marketplace_compatibility(mock_check_helm_cli):
    """Test check_marketplace_compatibility function."""
    mock_check_helm_cli.return_value = True
    compat = check_marketplace_compatibility()
    assert compat["cursor"] is True
    assert len(compat["reasons"]) == 0

    mock_check_helm_cli.return_value = False
    compat = check_marketplace_compatibility()
    assert compat["cursor"] is False
    assert "Helm CLI not installed" in compat["reasons"]


@mock.patch("pathlib.Path")
@mock.patch("tempfile.gettempdir")
@mock.patch("mcp_chart_scanner.server.mcp_server.os")
@mock.patch("mcp_chart_scanner.server.mcp_server.check_helm_cli")
def test_check_marketplace_compatibility_python_version(
    mock_check_helm_cli, mock_os, mock_gettempdir, mock_path
):
    """Test check_marketplace_compatibility function with different Python versions."""
    mock_check_helm_cli.return_value = True

    mock_gettempdir.return_value = "/tmp"
    mock_temp_file = mock.MagicMock()
    mock_path.return_value.__truediv__.return_value = mock_temp_file

    with mock.patch(
        "sys.version_info", new=type("obj", (object,), {"major": 3, "minor": 7})
    ):
        compat = check_marketplace_compatibility()
        assert compat["cursor"] is False
        assert "Python version 3.7 not supported" in compat["reasons"][0]

    with mock.patch(
        "sys.version_info", new=type("obj", (object,), {"major": 3, "minor": 8})
    ):
        compat = check_marketplace_compatibility()
        assert compat["cursor"] is True
        assert len(compat["reasons"]) == 0

    compat = check_marketplace_compatibility()
    assert compat["cursor"] is True
    assert len(compat["reasons"]) == 0


@mock.patch("mcp_chart_scanner.server.mcp_server.os")
@mock.patch("mcp_chart_scanner.server.mcp_server.sys")
@mock.patch("mcp_chart_scanner.server.mcp_server.check_helm_cli")
def test_check_marketplace_compatibility_cursor_env(
    mock_check_helm_cli, mock_sys, mock_os
):
    """Test check_marketplace_compatibility in Cursor environment."""
    mock_check_helm_cli.return_value = True

    mock_sys.stdin.isatty.return_value = False
    mock_sys.stdout.isatty.return_value = False
    mock_os.environ.get.return_value = None

    compat = check_marketplace_compatibility()
    assert compat["cursor"] is True

    mock_sys.stdin.isatty.return_value = True
    mock_sys.stdout.isatty.return_value = True
    mock_os.environ.get.return_value = "cursor-env"

    compat = check_marketplace_compatibility()
    assert compat["cursor"] is True


@mock.patch("mcp_chart_scanner.server.mcp_server.check_helm_cli")
def test_check_marketplace_compatibility_filesystem(mock_check_helm_cli):
    """Test check_marketplace_compatibility with filesystem access issues."""
    mock_check_helm_cli.return_value = True

    compat = check_marketplace_compatibility()
    assert compat["cursor"] is True
    assert len(compat["reasons"]) == 0

    mock_check_helm_cli.return_value = False
    compat = check_marketplace_compatibility()
    assert compat["cursor"] is False
    assert "Helm CLI not installed" in compat["reasons"]
