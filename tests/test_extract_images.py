import os
import tempfile
import pytest
from pathlib import Path
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp_chart_image_scanner.extract_docker_images import (
    prepare_chart, helm_dependency_update, helm_template, collect_images
)

class TestExtractImages:
    def test_collect_images_from_yaml(self):
        test_yaml = """
        apiVersion: v1
        kind: Pod
        metadata:
          name: test-pod
        spec:
          containers:
          - name: test-container
            image: nginx:1.14.2
          - name: redis
            image: redis:6.0.5
          initContainers:
          - name: init-container
            image: busybox:1.33.1
        """
        
        images = collect_images(test_yaml)
        assert len(images) == 3
        assert "docker.io/library/nginx:1.14.2" in images
        assert "docker.io/library/redis:6.0.5" in images
        assert "docker.io/library/busybox:1.33.1" in images
