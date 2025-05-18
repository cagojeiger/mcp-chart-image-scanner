# Developer Guide

## Project Structure

The project follows a standard Python package structure:

```
mcp-chart-image-scanner/
├── docs/                 # Documentation
├── src/                  # Source code
│   └── mcp_chart_image_scanner/
│       ├── __init__.py
│       ├── main.py       # Main entry point
│       ├── mcp_server.py # MCP server implementation
│       └── extract_docker_images.py # Image extraction logic
├── tests/                # Test files
├── main.py               # Root-level entry point for easier local testing
├── setup.py              # Package setup
└── smithery.yaml         # Smithery.ai configuration
```

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/cagojeiger/mcp-chart-image-scanner.git
   cd mcp-chart-image-scanner
   ```

2. Install dependencies:
   ```bash
   uv pip install -e .
   ```

3. Install Helm (required for testing):
   ```bash
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
   ```

## Running Tests

```bash
pytest tests/
```

## Building the Docker Image

```bash
docker build -t mcp-chart-image-scanner .
```
