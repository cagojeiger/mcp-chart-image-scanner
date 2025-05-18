import os
import pytest
import sys
import asyncio
import json
from pathlib import Path
import httpx
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp_chart_image_scanner.mcp_server import app, mcp_server

client = TestClient(app)

class TestMCPTransport:
    def test_sse_endpoint_exists(self):
        """Test that the SSE endpoint exists in the FastAPI app"""
        response = client.get("/mcp-sse/sse")
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
    
    def test_sse_post_endpoint_exists(self):
        """Test that the SSE POST endpoint exists for client-to-server messages"""
        response = client.post("/mcp-sse/messages", 
                               json={
                                   "jsonrpc": "2.0",
                                   "id": 1,
                                   "method": "listTools",
                                   "params": {}
                               })
        assert response.status_code in [200, 202], "SSE POST endpoint should accept JSON-RPC messages"
    
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
    
    def test_list_tools_api(self):
        """Test that we can list tools through API (transport-agnostic)"""
        response = client.get("/mcp-sse/tools")
        assert response.status_code == 200
        tools = response.json()
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        tool_names = [tool["name"] for tool in tools]
        assert "extract_from_path" in tool_names
        assert "extract_from_upload" in tool_names
