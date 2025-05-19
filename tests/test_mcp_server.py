"""Tests for the MCP server module."""

from unittest import mock

import pytest
import requests
from fastmcp import FastMCP

from mcp_chart_scanner.server.mcp_server import (
    check_helm_cli,
    check_marketplace_compatibility,
    main,
    mcp,
    parse_args,
    scan_chart_path,
    scan_chart_url,
)


def test_mcp_server_initialization():
    """Test MCP server initialization."""
    assert isinstance(mcp, FastMCP)
    assert mcp.name == "Chart Image Scanner"


@pytest.mark.asyncio
@mock.patch("mcp_chart_scanner.server.mcp_server.extract_images_from_chart")
@mock.patch("os.path.exists")
async def test_scan_chart_path(mock_exists, mock_extract_images):
    """Test scan_chart_path function."""
    mock_extract_images.return_value = ["image1", "image2"]
    mock_exists.return_value = True  # Mock path exists to avoid FileNotFoundError

    mock_ctx = mock.AsyncMock()

    result = await scan_chart_path(
        path="chart.tgz",
        values_files=["values.yaml"],
        normalize=True,
        ctx=mock_ctx,
    )

    mock_extract_images.assert_called_once_with(
        chart_path="chart.tgz",
        values_files=["values.yaml"],
        normalize=True,
    )
    mock_ctx.info.assert_has_calls(
        [
            mock.call("Scanning chart at path: chart.tgz"),
            mock.call("Found 2 images"),
        ]
    )
    assert result == ["image1", "image2"]


@pytest.mark.asyncio
@mock.patch("mcp_chart_scanner.server.mcp_server.requests.get")
@mock.patch("mcp_chart_scanner.server.mcp_server.extract_images_from_chart")
async def test_scan_chart_url(mock_extract_images, mock_requests_get):
    """Test scan_chart_url function."""
    mock_extract_images.return_value = ["image1", "image2"]

    mock_response = mock.MagicMock()
    mock_response.iter_content.return_value = [b"data"]
    mock_requests_get.return_value = mock_response

    mock_ctx = mock.AsyncMock()

    mock_temp_file = mock.MagicMock()
    mock_temp_file.name = "temp.tgz"
    mock_temp_file.__enter__.return_value = mock_temp_file

    with mock.patch("tempfile.NamedTemporaryFile", return_value=mock_temp_file):
        result = await scan_chart_url(
            url="http://example.com/chart.tgz",
            values_files=["values.yaml"],
            normalize=True,
            ctx=mock_ctx,
        )

    mock_requests_get.assert_called_once_with(
        "http://example.com/chart.tgz", stream=True, timeout=30
    )
    mock_response.raise_for_status.assert_called_once()
    mock_extract_images.assert_called_once_with(
        chart_path="temp.tgz",
        values_files=["values.yaml"],
        normalize=True,
    )
    mock_ctx.info.assert_has_calls(
        [
            mock.call("Downloading chart from URL: http://example.com/chart.tgz"),
            mock.call("Downloaded chart to: temp.tgz"),
            mock.call("Found 2 images"),
        ],
        any_order=True,
    )
    assert result == ["image1", "image2"]


def test_parse_args():
    """Test parse_args function."""
    with mock.patch("sys.argv", ["chart-scanner-server"]):
        args = parse_args()
        assert args.transport == "stdio"
        assert not args.quiet

    with mock.patch(
        "sys.argv",
        [
            "chart-scanner-server",
            "--transport",
            "stdio",
            "--quiet",
        ],
    ):
        args = parse_args()
        assert args.transport == "stdio"
        assert args.quiet


@mock.patch("subprocess.run")
def test_check_helm_cli_success(mock_run):
    """Test check_helm_cli function when Helm CLI is installed."""
    mock_process = mock.MagicMock()
    mock_process.stdout = "version.BuildInfo"
    mock_run.return_value = mock_process

    result = check_helm_cli()

    mock_run.assert_called_once_with(
        ["helm", "version"],
        check=True,
        stdout=mock.ANY,
        stderr=mock.ANY,
        text=True,
    )
    assert result is True


@mock.patch("subprocess.run")
def test_check_helm_cli_failure(mock_run):
    """Test check_helm_cli function when Helm CLI is not installed."""
    mock_run.side_effect = FileNotFoundError("No such file or directory: 'helm'")

    result = check_helm_cli()

    mock_run.assert_called_once_with(
        ["helm", "version"],
        check=True,
        stdout=mock.ANY,
        stderr=mock.ANY,
        text=True,
    )
    assert result is False


@mock.patch("mcp_chart_scanner.server.mcp_server.mcp.run")
@mock.patch("mcp_chart_scanner.server.mcp_server.check_helm_cli")
@mock.patch("mcp_chart_scanner.server.mcp_server.parse_args")
def test_main_helm_cli_not_installed(
    mock_parse_args, mock_check_helm_cli, mock_mcp_run
):
    """Test main function when Helm CLI is not installed."""
    mock_args = mock.MagicMock()
    mock_args.transport = "stdio"
    mock_args.quiet = False
    mock_parse_args.return_value = mock_args

    mock_check_helm_cli.return_value = False

    with (
        mock.patch("sys.exit") as mock_exit,
        mock.patch("builtins.print") as mock_print,
    ):
        main()

        mock_check_helm_cli.assert_called_once()
        mock_print.assert_has_calls(
            [
                mock.call("오류: Helm CLI가 설치되어 있지 않습니다."),
                mock.call("Helm CLI 설치 방법: https://helm.sh/docs/intro/install/"),
            ]
        )
        mock_exit.assert_called_once_with(1)
        mock_mcp_run.assert_not_called()


@mock.patch("mcp_chart_scanner.server.mcp_server.mcp.run")
@mock.patch("mcp_chart_scanner.server.mcp_server.check_helm_cli")
@mock.patch("mcp_chart_scanner.server.mcp_server.parse_args")
def test_main_stdio(mock_parse_args, mock_check_helm_cli, mock_mcp_run):
    """Test main function with stdio transport."""
    mock_args = mock.MagicMock()
    mock_args.transport = "stdio"
    mock_args.quiet = False
    mock_parse_args.return_value = mock_args

    mock_check_helm_cli.return_value = True

    main()

    mock_check_helm_cli.assert_called_once()
    mock_mcp_run.assert_called_once_with(transport="stdio")


@mock.patch("mcp_chart_scanner.server.mcp_server.sys.exit")
@mock.patch("mcp_chart_scanner.server.mcp_server.check_helm_cli")
@mock.patch("mcp_chart_scanner.server.mcp_server.parse_args")
def test_main_unsupported_transport(mock_parse_args, mock_check_helm_cli, mock_exit):
    """Test main function with unsupported transport."""
    mock_args = mock.MagicMock()
    mock_args.transport = "unsupported"
    mock_args.quiet = False
    mock_parse_args.return_value = mock_args

    mock_check_helm_cli.return_value = True

    main()

    mock_check_helm_cli.assert_called_once()
    mock_exit.assert_called_once_with(1)


@pytest.mark.asyncio
@mock.patch("mcp_chart_scanner.server.mcp_server.extract_images_from_chart")
async def test_scan_chart_path_file_not_found(mock_extract_images):
    """Test scan_chart_path function with non-existent path."""
    mock_ctx = mock.AsyncMock()

    with mock.patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError) as excinfo:
            await scan_chart_path(
                path="nonexistent.tgz",
                ctx=mock_ctx,
            )

        assert "Chart path not found" in str(excinfo.value)
        mock_ctx.error.assert_called_once()
        mock_extract_images.assert_not_called()


@pytest.mark.asyncio
@mock.patch("mcp_chart_scanner.server.mcp_server.requests.get")
async def test_scan_chart_url_request_exception(mock_requests_get):
    """Test scan_chart_url function with request exception."""
    mock_requests_get.side_effect = requests.RequestException("Connection error")
    mock_ctx = mock.AsyncMock()

    with pytest.raises(ValueError) as excinfo:
        await scan_chart_url(
            url="http://example.com/chart.tgz",
            ctx=mock_ctx,
        )

    assert "Failed to download chart" in str(excinfo.value)
    mock_ctx.error.assert_called_once()


@pytest.mark.asyncio
async def test_scan_chart_url_invalid_url_format():
    """Test scan_chart_url function with invalid URL format."""
    mock_ctx = mock.AsyncMock()

    with pytest.raises(ValueError) as excinfo:
        await scan_chart_url(
            url="ftp://example.com/chart.tgz",
            ctx=mock_ctx,
        )

    assert "Invalid URL format:" in str(excinfo.value)
    assert "must start with http:// or https://" in str(excinfo.value)
    mock_ctx.error.assert_called_once()


@pytest.mark.asyncio
@mock.patch("os.unlink")
@mock.patch("mcp_chart_scanner.server.mcp_server.extract_images_from_chart")
async def test_temp_file_cleanup(mock_extract_images, mock_unlink):
    """Test temporary file cleanup after chart processing."""
    mock_extract_images.return_value = ["image1", "image2"]
    mock_ctx = mock.AsyncMock()

    with (
        mock.patch(
            "mcp_chart_scanner.server.mcp_server.requests.get"
        ) as mock_requests_get,
        mock.patch("tempfile.NamedTemporaryFile") as mock_temp_file,
    ):
        mock_response = mock.MagicMock()
        mock_response.iter_content.return_value = [b"data"]
        mock_requests_get.return_value = mock_response

        mock_temp_file.return_value.__enter__.return_value.name = "temp.tgz"

        await scan_chart_url(
            url="http://example.com/chart.tgz",
            ctx=mock_ctx,
        )

    mock_unlink.assert_called_once_with("temp.tgz")
    mock_ctx.info.assert_any_call("Cleaned up temporary file: temp.tgz")


@mock.patch("mcp_chart_scanner.server.mcp_server.check_helm_cli")
def test_check_marketplace_compatibility(mock_check_helm_cli):
    """Test check_marketplace_compatibility function."""
    mock_check_helm_cli.return_value = True
    compat = check_marketplace_compatibility()
    assert compat["cursor"] is True
    assert compat["smithery"] is True
    assert len(compat["reasons"]) == 0

    mock_check_helm_cli.return_value = False
    compat = check_marketplace_compatibility()
    assert compat["cursor"] is False
    assert compat["smithery"] is False
    assert "Helm CLI not installed" in compat["reasons"]
