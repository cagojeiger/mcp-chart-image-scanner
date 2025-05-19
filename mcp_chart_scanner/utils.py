"""Utility functions and constants for Helm CLI checks."""

from __future__ import annotations

import logging
import subprocess

__all__ = [
    "ERROR_HELM_NOT_INSTALLED",
    "ERROR_HELM_INSTALL_GUIDE",
    "check_helm_cli",
]

logger = logging.getLogger(__name__)

ERROR_HELM_NOT_INSTALLED = "오류: Helm CLI가 설치되어 있지 않습니다."
"""Error message displayed when Helm CLI is missing."""

ERROR_HELM_INSTALL_GUIDE = "Helm CLI 설치 방법: https://helm.sh/docs/intro/install/"
"""Guide URL for installing Helm CLI."""


def check_helm_cli() -> bool:
    """Return ``True`` if Helm CLI is available.

    Returns:
        Whether the ``helm`` command is callable.
    """
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
        logger.error("Helm CLI check failed: %s", exc)
        return False

