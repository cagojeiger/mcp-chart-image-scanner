"""Tests for Helm CLI functionality."""

from unittest import mock

from mcp_chart_scanner.server.mcp_server import check_helm_cli


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
