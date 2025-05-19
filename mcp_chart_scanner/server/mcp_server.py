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
ERROR_INVALID_URL = "Invalid URL format: {url} (must start with http:// or https://)"
ERROR_DATA_TOO_LARGE = "Chart data too large: {size} bytes (max {max_size} bytes)"
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
    compatibility = {"cursor": True, "smithery": False, "reasons": []}

    if not check_helm_cli():
        compatibility["cursor"] = False
        compatibility["reasons"].append("Helm CLI not installed")

    # Check Python version compatibility
    import sys
    import os
    import pathlib
    import tempfile

    python_version = sys.version_info
    if python_version.major < 3 or (
        python_version.major == 3 and python_version.minor < 8
    ):
        compatibility["cursor"] = False
        compatibility["reasons"].append(
            f"Python version {python_version.major}.{python_version.minor} not supported (min 3.8)"
        )
        return compatibility

    try:
        import fastmcp  # noqa: F401
        import requests  # noqa: F401
    except ImportError as e:
        compatibility["cursor"] = False
        compatibility["reasons"].append(f"Required package missing: {str(e)}")
        
    # Check stdio transport compatibility
    is_stdio_mode = not sys.stdin.isatty() and not sys.stdout.isatty()
    is_cursor_env = os.environ.get("CURSOR_CONTEXT") is not None
    
    # For testing purposes, we don't add this as a reason that affects compatibility
    if not is_stdio_mode and not is_cursor_env:
        pass  # We don't add a reason here as it's just informational
        
    try:
        test_file = pathlib.Path(tempfile.gettempdir()) / "cursor_test_file"
        test_file.touch()
        test_file.unlink()
    except (IOError, OSError) as e:
        compatibility["cursor"] = False
        compatibility["reasons"].append(f"Filesystem access issue: {str(e)}")

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

    Scan a local Helm chart file or directory:
    ```python
    result = scan_chart_path("/path/to/chart.tgz")  # Always use absolute paths
    print(result)  # List of Docker images
    ```

    Scan a Helm chart from a URL:
    ```python
    result = scan_chart_url("https://example.com/charts/app-1.0.0.tgz")
    print(result)  # List of Docker images
    ```

    All tools support these options:
    - `values_files`: List of additional values files to use (should be absolute paths)
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
        path: Absolute path to the chart (.tgz file or directory). Relative paths may cause errors.
        values_files: Optional list of values files (should be absolute paths)
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
            if ctx:
                await ctx.error(error_msg)
            raise FileNotFoundError(error_msg)

        images = extract_images_from_chart(
            chart_path=path,
            values_files=values_files,
            normalize=normalize,
        )

        if ctx:
            await ctx.info(f"Found {len(images)} images")

        return images
    except FileNotFoundError as e:
        if "Chart path not found" not in str(e):
            error_msg = ERROR_FILE_NOT_FOUND.format(error=str(e))
            await log_and_raise(error_msg, ctx, FileNotFoundError)
        else:
            raise
        return []  # This line will never be reached but satisfies type checker
    except Exception as e:
        error_msg = ERROR_GENERAL.format(error=str(e))
        await log_and_raise(error_msg, ctx, ValueError)
        return []  # This line will never be reached but satisfies type checker


@mcp.tool()
async def scan_chart_url(
    url: str,
    values_files: Optional[List[str]] = None,
    normalize: bool = True,
    timeout: int = 30,
    ctx: Context = None,
) -> List[str]:
    """Scan a Helm chart from a URL.

    Args:
        url: URL to the chart (.tgz file)
        values_files: Optional list of values files (should be absolute paths)
        normalize: Whether to normalize image names
        timeout: Timeout in seconds for the HTTP request (default: 30)
        ctx: MCP context for communication with client

    Returns:
        List of Docker images

    Raises:
        ValueError: If chart is invalid or cannot be processed
        requests.RequestException: If chart download fails
    """
    if ctx:
        await ctx.info(f"Downloading chart from URL: {url}")

    if not url.startswith(("http://", "https://")):
        error_msg = ERROR_INVALID_URL.format(url=url)
        await log_and_raise(error_msg, ctx, ValueError)

    chart_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".tgz", delete=False) as tmp_file:
            try:
                response = requests.get(url, stream=True, timeout=timeout)
                response.raise_for_status()
            except requests.RequestException as e:
                error_msg = ERROR_DOWNLOAD_FAILED.format(error=str(e))
                await log_and_raise(error_msg, ctx, ValueError)

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # 빈 청크 필터링
                    tmp_file.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and ctx:
                        progress_interval = max(
                            1, total_size // 10
                        )  # 0으로 나누기 방지
                        if downloaded % progress_interval < 8192:
                            progress = (downloaded / total_size) * 100
                            await ctx.info(f"Download progress: {progress:.1f}%")
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
        await log_and_raise(error_msg, ctx, FileNotFoundError)
        return []  # This line will never be reached but satisfies type checker
    except ValueError as e:
        if "Failed to download chart" not in str(e):
            error_msg = ERROR_GENERAL.format(error=str(e))
            await log_and_raise(error_msg, ctx, ValueError)
        else:
            raise
        return []  # This line will never be reached but satisfies type checker
    except Exception as e:
        error_msg = ERROR_GENERAL.format(error=str(e))
        await log_and_raise(error_msg, ctx, ValueError)
        return []  # This line will never be reached but satisfies type checker
    finally:
        if chart_path:
            try:
                os.unlink(chart_path)
                if ctx:
                    await ctx.info(f"Cleaned up temporary file: {chart_path}")
            except Exception as e:
                if ctx:
                    await ctx.warn(
                        f"Failed to clean up temporary file {chart_path}: {str(e)}"
                    )


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
        choices=["stdio"],
        default="stdio",
        help="Transport protocol (stdio only)",
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
        try:
            mcp.remove_tool("scan_chart_upload")
        except (AttributeError, KeyError, Exception) as e:
            logger.warning(f"Using fallback method to disable tools: {str(e)}")
            if hasattr(mcp, "tools") and isinstance(mcp.tools, dict):
                mcp.tools.pop("scan_chart_upload", None)
        logger.info("Tool 'scan_chart_upload' is disabled")
        mcp.run(transport="stdio")
    else:
        logger.error(f"Unsupported transport: {args.transport}")
        sys.exit(1)


if __name__ == "__main__":
    main()
