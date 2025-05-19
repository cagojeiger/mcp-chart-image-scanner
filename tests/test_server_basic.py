"""Tests for basic MCP server functionality."""

from unittest import mock

from fastmcp import FastMCP

from mcp_chart_scanner.server.mcp_server import mcp, parse_args


def test_mcp_server_initialization():
    """Test MCP server initialization."""
    assert isinstance(mcp, FastMCP)
    assert mcp.name == "Chart Image Scanner"


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
