"""Tests for the main function."""

from unittest import mock

from mcp_chart_scanner.server.mcp_server import main


@mock.patch("mcp_chart_scanner.server.mcp_server.mcp.run")
@mock.patch("mcp_chart_scanner.server.mcp_server.check_helm_cli")
@mock.patch("mcp_chart_scanner.server.mcp_server.parse_args")
def test_main_helm_cli_not_installed(
    mock_parse_args: mock.MagicMock,
    mock_check_helm_cli: mock.MagicMock,
    mock_mcp_run: mock.MagicMock,
) -> None:
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
def test_main_stdio(
    mock_parse_args: mock.MagicMock,
    mock_check_helm_cli: mock.MagicMock,
    mock_mcp_run: mock.MagicMock,
) -> None:
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
def test_main_unsupported_transport(
    mock_parse_args: mock.MagicMock,
    mock_check_helm_cli: mock.MagicMock,
    mock_exit: mock.MagicMock,
) -> None:
    """Test main function with unsupported transport."""
    mock_args = mock.MagicMock()
    mock_args.transport = "unsupported"
    mock_args.quiet = False
    mock_parse_args.return_value = mock_args

    mock_check_helm_cli.return_value = True

    main()

    mock_check_helm_cli.assert_called_once()
    mock_exit.assert_called_once_with(1)
