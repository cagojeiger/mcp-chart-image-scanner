"""
Health check functionality for the MCP Chart Image Scanner.

This module provides a simple HTTP server for health checks when running in Docker.
"""
import http.server
import socketserver
import threading
import json
import logging

logger = logging.getLogger(__name__)

class HealthHandler(http.server.SimpleHTTPRequestHandler):
    """Handler for health check requests."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "healthy", "service": "mcp-chart-image-scanner"}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found')
