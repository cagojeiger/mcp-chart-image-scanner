"""Tests for error handling functionality."""

import subprocess
from unittest import mock

import pytest
import requests

from mcp_chart_scanner.server.mcp_server import scan_chart_path, scan_chart_url


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
@mock.patch("mcp_chart_scanner.server.mcp_server.extract_images_from_chart")
@mock.patch("os.path.exists")
async def test_scan_chart_path_invalid_format(mock_exists, mock_extract_images):
    """Test scan_chart_path with invalid chart format."""
    mock_exists.return_value = True
    mock_extract_images.side_effect = ValueError("Unsupported chart format")
    mock_ctx = mock.AsyncMock()

    with pytest.raises(ValueError) as excinfo:
        await scan_chart_path(
            path="/path/to/invalid.txt",
            ctx=mock_ctx,
        )

    assert "Unsupported chart format" in str(
        excinfo.value
    ) or "Error processing chart" in str(excinfo.value)
    mock_ctx.error.assert_called_once()


@pytest.mark.asyncio
@mock.patch("mcp_chart_scanner.server.mcp_server.extract_images_from_chart")
@mock.patch("os.path.exists")
async def test_scan_chart_path_values_file_not_found(mock_exists, mock_extract_images):
    """Test scan_chart_path with non-existent values file."""
    mock_exists.return_value = True
    mock_extract_images.side_effect = FileNotFoundError("Values file not found")
    mock_ctx = mock.AsyncMock()

    with pytest.raises(FileNotFoundError) as excinfo:
        await scan_chart_path(
            path="/path/to/chart.tgz",
            values_files=["/nonexistent/values.yaml"],
            ctx=mock_ctx,
        )

    assert "File not found" in str(excinfo.value)
    mock_ctx.error.assert_called_once()


@pytest.mark.asyncio
@mock.patch("mcp_chart_scanner.server.mcp_server.extract_images_from_chart")
@mock.patch("os.path.exists")
async def test_scan_chart_path_helm_cli_error(mock_exists, mock_extract_images):
    """Test scan_chart_path with Helm CLI error."""
    mock_exists.return_value = True
    mock_extract_images.side_effect = subprocess.CalledProcessError(1, "helm template")
    mock_ctx = mock.AsyncMock()

    with pytest.raises(ValueError) as excinfo:
        await scan_chart_path(
            path="/path/to/chart.tgz",
            ctx=mock_ctx,
        )

    assert "Error processing chart" in str(excinfo.value)
    mock_ctx.error.assert_called_once()


@pytest.mark.asyncio
@mock.patch("mcp_chart_scanner.server.mcp_server.extract_images_from_chart")
@mock.patch("os.path.exists")
async def test_scan_chart_path_missing_chart_yaml(mock_exists, mock_extract_images):
    """Test scan_chart_path function with missing Chart.yaml."""
    mock_extract_images.side_effect = ValueError("Not a valid Helm chart directory")

    mock_exists.return_value = True
    mock_ctx = mock.AsyncMock()

    with pytest.raises(ValueError) as excinfo:
        await scan_chart_path(
            path="/invalid/chart/dir",
            ctx=mock_ctx,
        )

    assert "Not a valid Helm chart directory" in str(
        excinfo.value
    ) or "Error processing chart" in str(excinfo.value)
    mock_ctx.error.assert_called_once()
    mock_extract_images.assert_called_once()
