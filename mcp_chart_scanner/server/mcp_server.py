"""MCP server for extracting Docker images from Helm charts."""

import argparse
import logging
import os
import pathlib
import sys
import tempfile
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

import requests
from fastmcp import Context, FastMCP, Image

from mcp_chart_scanner.extract import extract_images_from_chart

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


mcp = FastMCP("Chart Image Scanner")


@mcp.resource("help://usage")
def get_usage() -> str:
    """Get usage information."""
    return """
    Chart Image Scanner
    ------------------
    
    This tool extracts Docker images from Helm charts.
    
    Available tools:
    - scan_chart_path: Scan a local chart path
    - scan_chart_url: Scan a chart from a URL
    - scan_chart_upload: Scan an uploaded chart file
    
    Example:
    ```
    result = scan_chart_path("/path/to/chart.tgz")
    print(result)
    ```
    """


@mcp.tool()
async def scan_chart_path(
    path: str,
    values_files: Optional[List[str]] = None,
    normalize: bool = True,
    ctx: Context = None,
) -> List[str]:
    """Scan a local Helm chart for Docker images.

    Args:
        path: Path to the chart (.tgz file or directory)
        values_files: Optional list of values files
        normalize: Whether to normalize image names

    Returns:
        List of Docker images
    """
    if ctx:
        await ctx.info(f"Scanning chart at path: {path}")

    try:
        images = extract_images_from_chart(
            chart_path=path,
            values_files=values_files,
            normalize=normalize,
        )

        if ctx:
            await ctx.info(f"Found {len(images)} images")

        return images
    except Exception as e:
        error_msg = f"Error scanning chart: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        raise ValueError(error_msg)


@mcp.tool()
async def scan_chart_url(
    url: str,
    values_files: Optional[List[str]] = None,
    normalize: bool = True,
    ctx: Context = None,
) -> List[str]:
    """Scan a Helm chart from a URL.

    Args:
        url: URL to the chart (.tgz file)
        values_files: Optional list of values files
        normalize: Whether to normalize image names

    Returns:
        List of Docker images
    """
    if ctx:
        await ctx.info(f"Downloading chart from URL: {url}")

    try:
        with tempfile.NamedTemporaryFile(suffix=".tgz", delete=False) as tmp_file:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            tmp_file.flush()

            chart_path = tmp_file.name

        try:
            if ctx:
                await ctx.info(f"Downloaded chart to: {chart_path}")

            images = extract_images_from_chart(
                chart_path=chart_path,
                values_files=values_files,
                normalize=normalize,
            )

            if ctx:
                await ctx.info(f"Found {len(images)} images")

            return images
        finally:
            try:
                os.unlink(chart_path)
            except Exception:
                pass
    except Exception as e:
        error_msg = f"Error scanning chart from URL: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        raise ValueError(error_msg)


@mcp.tool()
async def scan_chart_upload(
    chart_data: bytes,
    values_files: Optional[List[str]] = None,
    normalize: bool = True,
    ctx: Context = None,
) -> List[str]:
    """Scan an uploaded Helm chart.

    Args:
        chart_data: Chart file content (bytes)
        values_files: Optional list of values files
        normalize: Whether to normalize image names

    Returns:
        List of Docker images
    """
    if ctx:
        await ctx.info(f"Processing uploaded chart ({len(chart_data)} bytes)")

    try:
        with tempfile.NamedTemporaryFile(suffix=".tgz", delete=False) as tmp_file:
            tmp_file.write(chart_data)
            tmp_file.flush()

            chart_path = tmp_file.name

        try:
            images = extract_images_from_chart(
                chart_path=chart_path,
                values_files=values_files,
                normalize=normalize,
            )

            if ctx:
                await ctx.info(f"Found {len(images)} images")

            return images
        finally:
            try:
                os.unlink(chart_path)
            except Exception:
                pass
    except Exception as e:
        error_msg = f"Error scanning uploaded chart: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        raise ValueError(error_msg)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the MCP server.

    Returns:
        Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="Start the Chart Image Scanner MCP server",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol (stdio or sse)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (for sse transport)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (for sse transport)",
    )
    parser.add_argument(
        "--path",
        default="/sse",
        help="Path for SSE endpoint (for sse transport)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress log messages",
    )
    return parser.parse_args()


def check_helm_cli() -> bool:
    """Check if Helm CLI is installed.

    Returns:
        True if Helm CLI is installed, False otherwise
    """
    try:
        import subprocess

        subprocess.run(
            ["helm", "version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def main() -> None:
    """Main entry point for the MCP server."""
    args = parse_args()

    if not check_helm_cli():
        print("오류: Helm CLI가 설치되어 있지 않습니다.")
        print("Helm CLI 설치 방법: https://helm.sh/docs/intro/install/")
        sys.exit(1)
        return  # Add return to ensure no more code executes after sys.exit in tests

    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)

    if args.transport == "stdio":
        logger.info("Starting MCP server with stdio transport")
        mcp.run(transport="stdio")
    elif args.transport == "sse":
        logger.info(
            f"Starting MCP server with SSE transport on {args.host}:{args.port}{args.path}"
        )
        mcp.run(
            transport="sse",
            host=args.host,
            port=args.port,
            path=args.path,
        )
    else:
        logger.error(f"Unsupported transport: {args.transport}")
        sys.exit(1)


if __name__ == "__main__":
    main()
