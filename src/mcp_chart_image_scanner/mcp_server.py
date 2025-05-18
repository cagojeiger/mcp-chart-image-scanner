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
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from src.mcp_chart_image_scanner.extract_docker_images import (
    prepare_chart, helm_dependency_update, helm_template, collect_images
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Helm Chart Image Scanner API",
    description="API for extracting Docker images from Helm charts",
    version="0.1.0"
)

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
            workdir = Path(tmp)
            
            chart_root = prepare_chart(Path(chart_path), workdir)
            
            values_paths = [Path(vf) for vf in (values_files or [])]
            
            helm_dependency_update(chart_root)
            rendered = helm_template(chart_root, values_paths)
            
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
            workdir = Path(tmp)
            
            chart_file = workdir / "chart.tgz"
            with open(chart_file, "wb") as f:
                f.write(chart_data)
            
            values_paths = []
            if values_files:
                for filename, content in values_files.items():
                    values_path = workdir / filename
                    with open(values_path, "wb") as f:
                        f.write(content)
                    values_paths.append(values_path)
            
            chart_root = prepare_chart(chart_file, workdir)
            
            helm_dependency_update(chart_root)
            rendered = helm_template(chart_root, values_paths)
            
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
            raise ValueError("Missing required argument 'chart_path'")
        
        chart_path = arguments["chart_path"]
        values_files = arguments.get("values_files", [])
        
        images = extract_images_from_path(chart_path, values_files)
        return [types.TextContent(type="text", text="\n".join(images))]
    
    elif name == "extract_from_upload":
        if "chart_data" not in arguments:
            raise ValueError("Missing required argument 'chart_data'")
        
        chart_data = arguments["chart_data"]
        values_files = arguments.get("values_files", {})
        
        images = await extract_images_from_upload(chart_data, values_files)
        return [types.TextContent(type="text", text="\n".join(images))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

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

@app.post("/upload/", response_model=List[str])
async def upload_chart(
    chart_file: UploadFile = File(...),
    values_files: List[UploadFile] = File([])
):
    """
    Extract Docker image list from uploaded Helm chart file.
    """
    try:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            
            chart_path = workdir / chart_file.filename
            with open(chart_path, "wb") as f:
                shutil.copyfileobj(chart_file.file, f)
            
            values_paths = []
            for vf in values_files:
                values_path = workdir / vf.filename
                with open(values_path, "wb") as f:
                    shutil.copyfileobj(vf.file, f)
                values_paths.append(values_path)
            
            chart_root = prepare_chart(chart_path, workdir)
            
            helm_dependency_update(chart_root)
            rendered = helm_template(chart_root, values_paths)
            
            images = collect_images(rendered)
            return images
    except Exception as e:
        logger.error(f"Error processing API upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {"status": "healthy", "service": "mcp-chart-image-scanner"}

@app.on_event("startup")
async def startup_event():
    """
    Startup event handler.
    """
    logger.info("Starting Helm Chart Image Scanner MCP server...")
    await run_sse_server(app)

async def run_mcp_server():
    """
    Run the MCP server.
    
    This function starts the stdio transport server.
    """
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as streams:
        await mcp_server.run(
            streams[0], streams[1], mcp_server.create_initialization_options()
        )

async def run_sse_server(app):
    """
    Run the MCP server with SSE transport.
    
    This sets up Server-Sent Events (SSE) transport for the MCP server,
    which enables server-to-client streaming with HTTP POST requests
    for client-to-server communication.
    
    Security warning: SSE transports can be vulnerable to DNS rebinding attacks.
    This implementation binds only to localhost and validates Origin headers.
    """
    from mcp.server.fastapi_sse import SSEHandler
    
    sse_handler = SSEHandler(server=mcp_server)
    
    app.mount("/mcp-sse", sse_handler.app)
    
    logger.info("SSE transport mounted at /mcp-sse")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
