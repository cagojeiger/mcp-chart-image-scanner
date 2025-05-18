"""
MCP Server for Helm Chart Image Scanner.

This module provides a Model Context Protocol (MCP) server that extracts Docker images
from Helm charts. It supports both local path-based extraction and file upload.
"""
import tempfile
import os
import sys
import shutil
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

import mcp.types as types
from mcp.server.lowlevel import Server

from src.mcp_chart_image_scanner.extract_docker_images import (
    prepare_chart, helm_dependency_update, helm_template, collect_images
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

mcp_server = Server("helm-chart-image-scanner")

def extract_images_from_path(chart_path: str, values_files: Optional[List[str]] = None) -> List[str]:
    """
    Extract Docker image list from a Helm chart path.
    
    Args:
        chart_path: Path to Helm chart (.tgz file or directory)
        values_files: List of additional values files paths (optional)
        
    Returns:
        List of extracted Docker images
    """
    try:
        with tempfile.TemporaryDirectory() as tmp:
            chart_dir = Path(tmp) / "chart"
            
            # Prepare the chart (extract if tgz or copy directory)
            chart_dir = prepare_chart(Path(chart_path), chart_dir)
            
            helm_dependency_update(chart_dir)
            
            values_paths = [Path(vf) for vf in (values_files or [])]
            rendered = helm_template(chart_dir, values_paths)
            
            images = collect_images(rendered)
            return images
    except Exception as e:
        logger.error(f"Error processing chart path: {str(e)}")
        return [f"Error: {str(e)}"]

async def extract_images_from_upload(chart_data: bytes, values_files: Optional[Dict[str, bytes]] = None) -> List[str]:
    """
    Extract Docker image list from uploaded Helm chart data.
    
    Args:
        chart_data: Uploaded chart file data (.tgz format)
        values_files: Dictionary of filename and data for additional values files (optional)
        
    Returns:
        List of extracted Docker images
    """
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            
            chart_file = tmp_path / "chart.tgz"
            with open(chart_file, "wb") as f:
                f.write(chart_data)
            
            chart_dir = tmp_path / "chart"
            chart_dir.mkdir(exist_ok=True)
            
            chart_dir = prepare_chart(chart_file, chart_dir)
            
            values_paths = []
            if values_files:
                for filename, data in values_files.items():
                    values_file = tmp_path / filename
                    with open(values_file, "wb") as f:
                        f.write(data)
                    values_paths.append(values_file)
            
            helm_dependency_update(chart_dir)
            
            rendered = helm_template(chart_dir, values_paths)
            
            images = collect_images(rendered)
            return images
    except Exception as e:
        logger.error(f"Error processing uploaded chart: {str(e)}")
        return [f"Error: {str(e)}"]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """
    Handle MCP tool calls.
    """
    if name == "extract_from_path":
        if "chart_path" not in arguments:
            return [types.TextContent("Error: Missing required parameter 'chart_path'")]
        
        chart_path = arguments["chart_path"]
        values_files = arguments.get("values_files")
        
        images = extract_images_from_path(chart_path, values_files)
        return [types.TextContent("\n".join(images))]
    
    elif name == "extract_from_upload":
        if "chart_data" not in arguments:
            return [types.TextContent("Error: Missing required parameter 'chart_data'")]
        
        chart_data = arguments["chart_data"]
        if isinstance(chart_data, str):
            chart_data = chart_data.encode()
        
        values_files = arguments.get("values_files")
        if values_files:
            values_dict = {k: v.encode() if isinstance(v, str) else v for k, v in values_files.items()}
        else:
            values_dict = None
        
        images = await extract_images_from_upload(chart_data, values_dict)
        return [types.TextContent("\n".join(images))]
    
    else:
        return [types.TextContent(f"Error: Unknown tool '{name}'")]

@mcp_server.list_tools()
async def list_tools() -> List[types.Tool]:
    """
    Return list of available MCP tools.
    """
    return [
        types.Tool(
            name="extract_from_path",
            description="Extract Docker image list from a Helm chart path",
            inputSchema={
                "type": "object",
                "required": ["chart_path"],
                "properties": {
                    "chart_path": {
                        "type": "string",
                        "description": "Path to Helm chart (.tgz file or directory)",
                    },
                    "values_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of additional values files paths (optional)",
                    },
                },
            },
        ),
        types.Tool(
            name="extract_from_upload",
            description="Extract Docker image list from uploaded Helm chart data",
            inputSchema={
                "type": "object",
                "required": ["chart_data"],
                "properties": {
                    "chart_data": {
                        "type": "string",
                        "format": "binary",
                        "description": "Uploaded chart file data (.tgz format)",
                    },
                    "values_files": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "string",
                            "format": "binary",
                        },
                        "description": "Dictionary of filename and data for additional values files (optional)",
                    },
                },
            },
        ),
    ]

async def run_mcp_server_stdio():
    """
    Run the MCP server with stdio transport.
    
    This function starts a stdio transport server for the MCP server,
    which enables communication through standard input and output streams.
    """
    try:
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as streams:
            await mcp_server.serve(
                streams[0], streams[1], mcp_server.create_initialization_options()
            )
    except ImportError as e:
        logger.error(f"stdio transport not available: {e}")
        raise

async def run_mcp_server_sse(host: str = "127.0.0.1", port: int = 8000):
    """
    Run the MCP server with SSE transport.
    
    This function starts a Server-Sent Events (SSE) transport server for the MCP server,
    which enables server-to-client streaming with HTTP POST requests for client-to-server
    communication.
    
    Security warning: SSE transports can be vulnerable to DNS rebinding attacks.
    This implementation binds only to localhost and validates Origin headers.
    
    Args:
        host: Hostname to bind to (default: 127.0.0.1)
        port: Port to listen on (default: 8000)
    """
    try:
        from mcp.server.sse import create_sse_app
        import uvicorn
        
        app = create_sse_app(mcp_server)
        config = uvicorn.Config(app, host=host, port=port)
        server = uvicorn.Server(config)
        await server.serve()
    except ImportError as e:
        logger.error(f"SSE transport not available: {e}")
        logger.warning("Continuing with stdio transport only.")

async def main(transport: str = "stdio", host: str = "127.0.0.1", port: int = 8000):
    """
    Main entry point for the MCP server.
    
    Args:
        transport: Transport method to use ('stdio', 'sse', or 'both')
        host: Hostname to bind to for SSE transport (default: 127.0.0.1)
        port: Port to listen on for SSE transport (default: 8000)
    """
    if transport == "stdio":
        await run_mcp_server_stdio()
    elif transport == "sse":
        await run_mcp_server_sse(host, port)
    elif transport == "both":
        import asyncio
        await asyncio.gather(
            run_mcp_server_stdio(), 
            run_mcp_server_sse(host, port)
        )
    else:
        raise ValueError(f"Unknown transport method: {transport}")

if __name__ == "__main__":
    import asyncio
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Chart Image Scanner")
    parser.add_argument("--transport", choices=["stdio", "sse", "both"], default="stdio", 
                        help="Transport method to use (default: stdio)")
    parser.add_argument("--host", default="127.0.0.1", 
                        help="Hostname to bind to for SSE transport (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, 
                        help="Port to listen on for SSE transport (default: 8000)")
    
    args = parser.parse_args()
    
    asyncio.run(main(args.transport, args.host, args.port))
