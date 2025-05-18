# User Guide

## Overview

MCP Chart Image Scanner is a Model Context Protocol (MCP) server that extracts Docker images from Helm charts. It supports both local path-based extraction and file upload methods.

## Installation

### Using Docker (Recommended)

```bash
# Build the Docker image
docker build -t mcp-chart-image-scanner .

# Run the Docker container
docker run -p 8000:8000 mcp-chart-image-scanner
```

### Installing Locally

```bash
# Install using uv
uv pip install -e .
```

## Usage

### Using the MCP Protocol

The MCP Chart Image Scanner supports two communication methods:

#### Using stdio Transport (Command Line)

You can use the MCP Chart Image Scanner with any MCP client by configuring it as follows:

```json
{
  "mcpServers": {
    "helm-chart-image-scanner": {
      "command": "python",
      "args": ["-m", "src.mcp_chart_image_scanner.main"]
    }
  }
}
```

#### Using SSE Transport (Web-based)

For web applications, you can use the SSE transport by connecting to the SSE endpoint:

```javascript
// Connect to the MCP server using SSE
const client = new MCPClient({
  transport: new SSETransport("http://127.0.0.1:8000/mcp-sse")
});

// List available tools
const tools = await client.listTools();
```

### Using as a REST API

Start the server:

```bash
python main.py
```

The server will be available at http://localhost:8000 with the following endpoints:

- `POST /upload/`: Upload a Helm chart file to extract Docker images
- `GET /health`: Health check endpoint

### Using with Smithery.ai

The MCP Chart Image Scanner can be registered with [Smithery.ai](https://smithery.ai) by providing the GitHub repository URL.
