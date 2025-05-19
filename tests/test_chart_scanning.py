"""Tests for chart scanning functionality."""

import pathlib
from unittest import mock

import pytest

from mcp_chart_scanner.extract import extract_images_from_chart
from mcp_chart_scanner.server.mcp_server import scan_chart_path, scan_chart_url


@pytest.mark.asyncio
@mock.patch("mcp_chart_scanner.server.mcp_server.extract_images_from_chart")
@mock.patch("os.path.exists")
async def test_scan_chart_path(
    mock_exists: mock.MagicMock, mock_extract_images: mock.MagicMock
) -> None:
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
async def test_scan_chart_url(
    mock_extract_images: mock.MagicMock, mock_requests_get: mock.MagicMock
) -> None:
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


@pytest.mark.asyncio
@mock.patch("os.unlink")
@mock.patch("mcp_chart_scanner.server.mcp_server.extract_images_from_chart")
async def test_temp_file_cleanup(
    mock_extract_images: mock.MagicMock, mock_unlink: mock.MagicMock
) -> None:
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


@pytest.mark.asyncio
@mock.patch("os.unlink")
@mock.patch("mcp_chart_scanner.server.mcp_server.extract_images_from_chart")
@mock.patch("mcp_chart_scanner.server.mcp_server.requests.get")
@mock.patch("tempfile.NamedTemporaryFile")
async def test_scan_chart_url_cleanup_exception(
    mock_temp_file: mock.MagicMock,
    mock_get: mock.MagicMock,
    mock_extract: mock.MagicMock,
    mock_unlink: mock.MagicMock,
) -> None:
    """Test scan_chart_url cleanup when unlink raises exception."""
    mock_response = mock.MagicMock()
    mock_response.iter_content.return_value = [b"data"]
    mock_get.return_value = mock_response
    mock_extract.return_value = ["image1", "image2"]

    mock_file = mock.MagicMock()
    mock_file.name = "temp.tgz"
    mock_file.__enter__.return_value = mock_file
    mock_temp_file.return_value = mock_file

    mock_unlink.side_effect = OSError("Permission denied")

    mock_ctx = mock.AsyncMock()

    result = await scan_chart_url(
        url="http://example.com/chart.tgz",
        ctx=mock_ctx,
    )

    assert result == ["image1", "image2"]
    mock_unlink.assert_called_once_with("temp.tgz")
    mock_ctx.warn.assert_called_once()
    assert "Failed to clean up temporary file" in mock_ctx.warn.call_args[0][0]


@pytest.mark.asyncio
@mock.patch("mcp_chart_scanner.extract.prepare_chart")
@mock.patch("mcp_chart_scanner.extract.helm_template")
@mock.patch("mcp_chart_scanner.extract.helm_dependency_update")
@mock.patch("mcp_chart_scanner.extract.collect_images")
async def test_extract_images_from_chart_tarball_format(
    mock_collect_images: mock.MagicMock,
    mock_helm_dependency_update: mock.MagicMock,
    mock_helm_template: mock.MagicMock,
    mock_prepare_chart: mock.MagicMock,
) -> None:
    """Test extract_images_from_chart with tarball format."""
    mock_tarball_path = pathlib.Path("/path/to/chart.tgz")
    mock_chart_dir = pathlib.Path("/tmp/extracted_chart")

    with mock.patch("tempfile.TemporaryDirectory"):
        mock_prepare_chart.return_value = mock_chart_dir
        mock_helm_template.return_value = "yaml: content"
        mock_collect_images.return_value = ["image1:tag1", "image2:tag2"]

        result = extract_images_from_chart(mock_tarball_path)

        assert result == ["image1:tag1", "image2:tag2"]
        mock_prepare_chart.assert_called_once()
        mock_helm_dependency_update.assert_called_once()
        mock_helm_template.assert_called_once()
        mock_collect_images.assert_called_once()


@pytest.mark.asyncio
@mock.patch("os.path.exists")
@mock.patch("mcp_chart_scanner.server.mcp_server.extract_images_from_chart")
async def test_scan_chart_path_directory_format(
    mock_extract_images: mock.MagicMock, mock_exists: mock.MagicMock
) -> None:
    """Test scan_chart_path with directory format."""
    mock_exists.return_value = True
    mock_extract_images.return_value = ["image1:tag1", "image2:tag2"]
    mock_ctx = mock.AsyncMock()

    result = await scan_chart_path(
        path="/path/to/chart/dir",
        ctx=mock_ctx,
    )

    assert result == ["image1:tag1", "image2:tag2"]
    mock_extract_images.assert_called_with(
        chart_path="/path/to/chart/dir",
        values_files=None,
        normalize=True,
    )
