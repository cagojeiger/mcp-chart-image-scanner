from mcp_chart_scanner.server.mcp_server import get_usage


def test_get_usage_not_empty():
    usage = get_usage()
    assert isinstance(usage, str)
    assert usage.strip() != ""
