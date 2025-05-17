import os
import pytest
import subprocess
import tempfile
import time
import requests
from pathlib import Path

class TestDockerImage:
    @pytest.fixture(scope="module")
    def docker_image(self):
        """도커 이미지를 빌드하고 컨테이너를 실행합니다."""
        repo_root = Path(__file__).parent.parent.absolute()
        
        build_cmd = ["docker", "build", "-t", "mcp-chart-image-scanner-test", str(repo_root)]
        subprocess.run(build_cmd, check=True)
        
        container_id = subprocess.check_output(
            ["docker", "run", "-d", "-p", "8000:8000", "mcp-chart-image-scanner-test"],
            text=True
        ).strip()
        
        time.sleep(5)
        
        yield container_id
        
        subprocess.run(["docker", "stop", container_id], check=True)
        subprocess.run(["docker", "rm", container_id], check=True)
    
    def test_server_health(self, docker_image):
        """서버가 실행 중인지 확인합니다."""
        response = requests.get("http://localhost:8000/docs")
        assert response.status_code == 200
        
    def test_upload_endpoint(self, docker_image):
        """업로드 엔드포인트가 작동하는지 확인합니다."""
        repo_root = Path(__file__).parent.parent.absolute()
        test_chart_dir = repo_root / "tests" / "test_data" / "charts" / "test-chart"
        
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            chart_tgz = tmp_path / "test-chart.tgz"
            
            subprocess.run(
                ["tar", "-czf", str(chart_tgz), "-C", str(test_chart_dir.parent), "test-chart"],
                check=True
            )
            
            with open(chart_tgz, "rb") as f:
                files = {"chart_file": ("test-chart.tgz", f)}
                response = requests.post("http://localhost:8000/upload/", files=files)
                
            assert response.status_code == 200
            assert isinstance(response.json(), list)
