"""MCP server for extracting Docker images from Helm charts."""

import argparse
import logging
import os
import sys
import tempfile
from importlib import metadata
from typing import Dict, List, Optional

import requests
from fastmcp import Context, FastMCP

from mcp_chart_scanner.extract import extract_images_from_chart

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

ERROR_CHART_NOT_FOUND = "Chart path not found: {path}"
ERROR_CHART_INVALID = "Invalid chart format: {error}"
ERROR_FILE_NOT_FOUND = "File not found: {error}"
ERROR_DOWNLOAD_FAILED = "Failed to download chart: {error}"
ERROR_EMPTY_UPLOAD = "Empty chart data received"
ERROR_GENERAL = "Error processing chart: {error}"
ERROR_HELM_NOT_INSTALLED = "오류: Helm CLI가 설치되어 있지 않습니다."
ERROR_HELM_INSTALL_GUIDE = "Helm CLI 설치 방법: https://helm.sh/docs/intro/install/"


async def log_and_raise(
    error_msg: str, ctx: Optional[Context] = None, exception_type=Exception
) -> None:
    """Log an error message to the context and raise an exception.

    Args:
        error_msg: Error message to log and raise
        ctx: MCP context for communication with client
        exception_type: Type of exception to raise (default: Exception)

    Raises:
        Exception: The specified exception type with the error message
    """
    if ctx:
        await ctx.error(error_msg)
    raise exception_type(error_msg)


def get_version() -> str:
    """Get the current package version.

    Returns:
        Package version string
    """
    try:
        return metadata.version("mcp-chart-scanner")
    except ImportError:
        return "unknown"


def check_marketplace_compatibility() -> Dict[str, bool]:
    """Check compatibility with different marketplaces.

    Returns:
        Dictionary of marketplace compatibility status
    """
    compatibility = {"cursor": True, "smithery": True, "reasons": []}

    if not check_helm_cli():
        compatibility["cursor"] = False
        compatibility["smithery"] = False
        compatibility["reasons"].append("Helm CLI not installed")

    # Check Python version compatibility
    import sys

    python_version = sys.version_info
    if python_version.major < 3 or (
        python_version.major == 3 and python_version.minor < 8
    ):
        compatibility["cursor"] = False
        compatibility["smithery"] = False
        compatibility["reasons"].append(
            f"Python version {python_version.major}.{python_version.minor} not supported (min 3.8)"
        )

    try:
        import fastmcp  # noqa: F401
        import requests  # noqa: F401
    except ImportError as e:
        compatibility["cursor"] = False
        compatibility["smithery"] = False
        compatibility["reasons"].append(f"Required package missing: {str(e)}")

    return compatibility


mcp = FastMCP("Chart Image Scanner")


@mcp.resource("help://usage")
def get_usage() -> str:
    """Get usage information."""
    return """
    # Chart Image Scanner

    This tool extracts Docker images from Helm charts. It supports multiple chart sources:
    - Local chart files (.tgz or directory)
    - Remote charts via URL
    - Uploaded chart files

    Scan a local Helm chart file or directory:
    ```python
    result = scan_chart_path("/path/to/chart.tgz")
    print(result)  # List of Docker images
    ```

    Scan a Helm chart from a URL:
    ```python
    result = scan_chart_url("https://example.com/charts/app-1.0.0.tgz")
    print(result)  # List of Docker images
    ```

    Scan an uploaded Helm chart:
    ```python
    result = scan_chart_upload(chart_data)
    print(result)  # List of Docker images
    ```

    All tools support these options:
    - `values_files`: List of additional values files to use
    - `normalize`: Whether to normalize image names (default: True)

    All tools provide detailed error messages. You can catch exceptions:
    ```python
    try:
        result = scan_chart_path("/nonexistent/path.tgz")
    except ValueError as e:
        print(f"Error: {e}")
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
        ctx: MCP context for communication with client

    Returns:
        List of Docker images

    Raises:
        ValueError: If chart is invalid or cannot be processed
        FileNotFoundError: If chart path or values files not found
    """
    if ctx:
        await ctx.info(f"Scanning chart at path: {path}")

    try:
        if not os.path.exists(path):
            error_msg = ERROR_CHART_NOT_FOUND.format(path=path)
            await log_and_raise(error_msg, ctx, FileNotFoundError)
            return []  # This line will never be reached due to the exception

        images = extract_images_from_chart(
            chart_path=path,
            values_files=values_files,
            normalize=normalize,
        )

        if ctx:
            await ctx.info(f"Found {len(images)} images")

        return images
    except FileNotFoundError as e:
        error_msg = ERROR_FILE_NOT_FOUND.format(error=str(e))
        await log_and_raise(error_msg, ctx, ValueError)
        return []  # This line will never be reached due to the exception
    except Exception as e:
        error_msg = ERROR_GENERAL.format(error=str(e))
        await log_and_raise(error_msg, ctx, ValueError)
        return []  # This line will never be reached due to the exception


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
        ctx: MCP context for communication with client

    Returns:
        List of Docker images

    Raises:
        ValueError: If chart is invalid or cannot be processed
        requests.RequestException: If chart download fails
    """
    if ctx:
        await ctx.info(f"Downloading chart from URL: {url}")

    chart_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".tgz", delete=False) as tmp_file:
            try:
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
            except requests.RequestException as e:
                error_msg = ERROR_DOWNLOAD_FAILED.format(error=str(e))
                await log_and_raise(error_msg, ctx, ValueError)
                return []  # This line will never be reached due to the exception

            for chunk in response.iter_content(chunk_size=8192):
                tmp_file.write(chunk)
            tmp_file.flush()

            chart_path = tmp_file.name

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
    except FileNotFoundError as e:
        error_msg = ERROR_FILE_NOT_FOUND.format(error=str(e))
        await log_and_raise(error_msg, ctx, ValueError)
        return []  # This line will never be reached due to the exception
    except Exception as e:
        error_msg = ERROR_GENERAL.format(error=str(e))
        await log_and_raise(error_msg, ctx, ValueError)
        return []  # This line will never be reached due to the exception
    finally:
        if chart_path:
            try:
                os.unlink(chart_path)
            except Exception:
                pass


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
        ctx: MCP context for communication with client

    Returns:
        List of Docker images

    Raises:
        ValueError: If chart is invalid or cannot be processed
        RuntimeError: If chart data is corrupted or invalid
    """
    if ctx:
        await ctx.info(f"Processing uploaded chart ({len(chart_data)} bytes)")

    if not chart_data:
        error_msg = ERROR_EMPTY_UPLOAD
        await log_and_raise(error_msg, ctx, ValueError)
        return []  # This line will never be reached due to the exception

    chart_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".tgz", delete=False) as tmp_file:
            tmp_file.write(chart_data)
            tmp_file.flush()

            chart_path = tmp_file.name

        images = extract_images_from_chart(
            chart_path=chart_path,
            values_files=values_files,
            normalize=normalize,
        )

        if ctx:
            await ctx.info(f"Found {len(images)} images")

        return images
    except FileNotFoundError as e:
        error_msg = ERROR_FILE_NOT_FOUND.format(error=str(e))
        await log_and_raise(error_msg, ctx, ValueError)
        return []  # This line will never be reached due to the exception
    except Exception as e:
        error_msg = ERROR_GENERAL.format(error=str(e))
        await log_and_raise(error_msg, ctx, ValueError)
        return []  # This line will never be reached due to the exception
    finally:
        if chart_path:
            try:
                os.unlink(chart_path)
            except Exception:
                pass


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

        process = subprocess.run(
            ["helm", "version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        version_info = process.stdout.strip()
        logger.info(f"Helm CLI detected: {version_info}")
        return True
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error(f"Helm CLI check failed: {str(e)}")
        return False


def main() -> None:
    """Main entry point for the MCP server."""
    args = parse_args()

    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    else:
        logging.getLogger().setLevel(logging.INFO)

    logger.info(f"Starting MCP Chart Image Scanner server v{get_version()}")

    if not check_helm_cli():
        print(ERROR_HELM_NOT_INSTALLED)
        print(ERROR_HELM_INSTALL_GUIDE)
        sys.exit(1)
        return  # Add return to ensure no more code executes after sys.exit in tests

    if args.transport == "stdio":
        logger.info("Starting MCP server with stdio transport")
        mcp.run(transport="stdio")
    elif args.transport == "sse":
        server_url = f"http://{args.host}:{args.port}{args.path}"
        logger.info(f"Starting MCP server with SSE transport on {server_url}")
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
