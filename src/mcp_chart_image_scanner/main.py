"""
Entry point for the MCP Chart Image Scanner server.

This module starts both the MCP server and the FastAPI server.
"""
import threading
import asyncio
import logging
import uvicorn

from src.mcp_chart_image_scanner.mcp_server import app, run_mcp_server

logger = logging.getLogger(__name__)


def start_mcp_server_thread():
    """
    Start the MCP server in a separate thread.
    
    This function starts the stdio transport server in a separate thread.
    The SSE transport is automatically initialized through the FastAPI startup event.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_mcp_server())


def main():
    """Main entry point for the application."""
    logger.info("Starting Helm Chart Image Scanner servers...")
    
    mcp_thread = threading.Thread(target=start_mcp_server_thread)
    mcp_thread.daemon = True
    mcp_thread.start()
    
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
