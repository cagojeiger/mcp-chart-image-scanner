#!/usr/bin/env python3
"""
Main entry point for MCP Chart Image Scanner.
This file allows running the scanner directly from the repository root.
"""
import sys
import os
import logging
import argparse

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.mcp_chart_image_scanner.main import main

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    main()
