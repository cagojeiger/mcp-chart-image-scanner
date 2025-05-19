import pathlib
from unittest import mock

from mcp_chart_scanner.cli import main
from mcp_chart_scanner.server.mcp_server import (
    ERROR_HELM_INSTALL_GUIDE,
    ERROR_HELM_NOT_INSTALLED,
)


@mock.patch("mcp_chart_scanner.cli.extract_images_from_chart")
@mock.patch("mcp_chart_scanner.cli.check_helm_cli")
@mock.patch("mcp_chart_scanner.cli.parse_cli_args")
def test_cli_main_helm_cli_not_installed(
    mock_parse_args: mock.MagicMock,
    mock_check_helm_cli: mock.MagicMock,
    mock_extract_images: mock.MagicMock,
) -> None:
    args = mock.MagicMock()
    args.chart = pathlib.Path("chart.tgz")
    args.values = []
    args.quiet = False
    args.json = False
    args.raw = False
    mock_parse_args.return_value = args
    mock_check_helm_cli.return_value = False

    with (
        mock.patch("sys.exit") as mock_exit,
        mock.patch("builtins.print") as mock_print,
    ):
        main()
        mock_check_helm_cli.assert_called_once()
        mock_print.assert_has_calls(
            [
                mock.call(ERROR_HELM_NOT_INSTALLED),
                mock.call(ERROR_HELM_INSTALL_GUIDE),
            ]
        )
        mock_exit.assert_called_once_with(1)
    mock_extract_images.assert_not_called()
