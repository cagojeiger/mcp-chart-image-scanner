import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import sys
import shutil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server import app, extract_images_from_path

client = TestClient(app)

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
    
    def test_upload_endpoint(self):
        """Test the FastAPI upload endpoint"""
        helm_path = shutil.which("helm")
        if not helm_path:
            pytest.skip("Helm is not installed, skipping test")
        
        response = client.post("/upload/")
        assert response.status_code == 422
        
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "mcp-chart-image-scanner"}
