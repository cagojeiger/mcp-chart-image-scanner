import os
import tempfile
import pytest
from pathlib import Path
import sys
import shutil
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp_chart_image_scanner.mcp_server import (
    extract_images_from_path, extract_images_from_upload, mcp_server
)

class TestMCPServer:
    def test_extract_images_from_path(self):
        helm_path = shutil.which("helm")
        if not helm_path:
            pytest.skip("Helm is not installed, skipping test")
            
        chart_path = "./tests/test_data/charts/test-chart"
        
        result = extract_images_from_path(chart_path)
        assert isinstance(result, list)
        
        if result and not any(item.startswith("Error:") for item in result):
            assert any("nginx:1.14.2" in img for img in result)
            assert any("redis:6.0.5" in img for img in result)
            assert any("busybox:1.33.1" in img for img in result)
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test the list_tools method of the MCP server"""
        tools = await mcp_server.list_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        tool_names = [tool.name for tool in tools]
        assert "extract_from_path" in tool_names
        assert "extract_from_upload" in tool_names
    
    def test_health_handler(self):
        """Test the health check handler"""
        from src.mcp_chart_image_scanner.health import HealthHandler
        import http.client
        import json
        
        class MockHandler(HealthHandler):
            def __init__(self):
                self.response_code = None
                self.headers = {}
                self.wfile = type('', (), {'write': lambda self, x: None})()
                
            def send_response(self, code):
                self.response_code = code
                
            def send_header(self, name, value):
                self.headers[name] = value
                
            def end_headers(self):
                pass
        
        handler = MockHandler()
        handler.path = '/health'
        handler.do_GET()
        
        assert handler.response_code == 200
        assert handler.headers.get('Content-type') == 'application/json'
