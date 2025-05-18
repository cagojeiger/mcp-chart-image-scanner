# Testing Guide

## Prerequisites

- Python 3.10+
- UV package manager
- Helm CLI
- Docker (optional, for container tests)

## Installing Test Dependencies

```bash
uv pip install pytest pytest-asyncio pytest-cov
```

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test Modules

```bash
# Test the image extraction functionality
pytest tests/test_extract_images.py

# Test the MCP server
pytest tests/test_mcp_server.py

# Test the Docker container (requires Docker)
pytest tests/test_docker.py
```

### Run Tests with Coverage Report

```bash
pytest tests/ --cov=src --cov-report=term-missing
```

## Manual Testing

### Testing the FastAPI Server

1. Start the server:
   ```bash
   python main.py
   ```

2. Visit http://localhost:8000/docs to access the Swagger UI.

3. Use the `/upload/` endpoint to upload a Helm chart and extract images.

### Testing the MCP Protocol

You can test the MCP protocol using either stdio or SSE transport:

#### Testing stdio Transport

```bash
python -m mcp.cli connect stdio -- python -m src.mcp_chart_image_scanner.main
```

#### Testing SSE Transport

Start the server:

```bash
python -m src.mcp_chart_image_scanner.main
```

Then connect to the SSE endpoint:

```bash
python -m mcp.cli connect sse --url http://127.0.0.1:8000/mcp-sse
```

You can also use browser developer tools to monitor SSE events by visiting `http://127.0.0.1:8000/mcp-sse/sse`.
