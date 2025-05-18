import os
import pytest
import sys
import asyncio
import json
from pathlib import Path
import mcp.types as types

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp_chart_image_scanner.mcp_server import mcp_server

class TestMCPTransport:
    @pytest.mark.asyncio
    async def test_call_tool(self):
        """Test calling a tool directly through the MCP server"""
        result = await mcp_server.call_tool("extract_from_path", {"chart_path": "./tests/test_data/charts/test-chart"})
        
        assert isinstance(result, list)
        assert all(isinstance(item, types.TextContent) for item in result)
        
        text_result = result[0].text if result else ""
        
        assert "nginx" in text_result
        assert "redis" in text_result
        assert "busybox" in text_result
    
    @pytest.mark.asyncio
    async def test_stdio_transport_initialization(self):
        """Test that the stdio transport can be initialized"""
        from mcp.server.stdio import stdio_server
        
        async def test_stdio():
            async with stdio_server() as streams:
                assert streams is not None
                assert len(streams) == 2
        
        try:
            await asyncio.wait_for(test_stdio(), timeout=2)
        except asyncio.TimeoutError:
            pytest.fail("Stdio transport initialization timed out")
    
    @pytest.mark.asyncio
    async def test_sse_transport_initialization(self):
        """Test that the SSE transport can be initialized"""
        try:
            from mcp.server.sse import create_sse_app
            
            app = create_sse_app(mcp_server)
            assert app is not None
        except ImportError:
            pytest.skip("SSE transport not available")
