"""
Entry point for the MCP Chart Image Scanner server.

This module starts the MCP server with the specified transport method.
"""
import os
import sys
import asyncio
import logging
import argparse

from src.mcp_chart_image_scanner.mcp_server import main as run_mcp_server
from src.mcp_chart_image_scanner.health import HealthHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def start_health_server(port: int = 8000):
    """Start a simple HTTP server for health checks."""
    import socketserver
    import threading
    
    handler = HealthHandler
    httpd = socketserver.TCPServer(("", port), handler)
    
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()
    
    logger.info(f"Health check server started on port {port}")

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="MCP Chart Image Scanner")
    parser.add_argument("--transport", choices=["stdio", "sse", "both"], default="both", 
                        help="Transport method to use (default: both)")
    parser.add_argument("--host", default="127.0.0.1", 
                        help="Hostname to bind to for SSE transport (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, 
                        help="Port to listen on for SSE transport and health checks (default: 8000)")
    parser.add_argument("--health", action="store_true", 
                        help="Start health check server (for Docker)")
    
    args = parser.parse_args()
    
    if args.health:
        start_health_server(args.port)
    
    asyncio.run(run_mcp_server(args.transport, args.host, args.port))

if __name__ == "__main__":
    main()
