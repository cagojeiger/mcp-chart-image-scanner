"""Utility functions for the chart scanner."""

from __future__ import annotations

import logging
import subprocess
import sys

ERROR_HELM_NOT_INSTALLED = "오류: Helm CLI가 설치되어 있지 않습니다."
ERROR_HELM_INSTALL_GUIDE = "Helm CLI 설치 방법: https://helm.sh/docs/intro/install/"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def check_helm_cli() -> bool:
    """Check if the Helm CLI is installed."""
    try:
        process = subprocess.run(
            ["helm", "version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        version_info = process.stdout.strip()
        logger.info("Helm CLI detected: %s", version_info)
        return True
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        logger.error("Helm CLI check failed: %s", str(exc))
        return False
