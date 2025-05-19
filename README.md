# MCP Chart Image Scanner

A tool for extracting Docker image references from Helm charts with CLI and MCP server support.

## Features

- Extract Docker image references from Helm charts (.tgz archives or directories)
- Command Line Interface (CLI) for local usage
- Model Context Protocol (MCP) server for integration with AI tools
- Support for multiple input methods:
  - Local file paths
  - File uploads
  - Remote URLs
- Support for stdio communication protocol
- Helm CLI included

## Installation

### From Source

```bash
git clone https://github.com/cagojeiger/mcp-chart-image-scanner.git
cd mcp-chart-image-scanner
pipx install -e .
```

> **주의**: 반드시 루트 디렉토리(`mcp-chart-image-scanner/`)에서 설치해야 합니다. 하위 디렉토리(`mcp_chart_scanner/`)에서 설치하면 실패합니다.
>
> **참고**: 일부 시스템에서는 "externally-managed-environment" 오류가 발생할 수 있습니다. 이 경우 가상 환경을 생성하거나 `--break-system-packages` 옵션을 사용하세요.
```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

설치가 완료되면 아래와 같이 `.cursor.json` 파일에 MCP 서버를 등록해 사용할 수 있습니다.

```json
{
  "mcpServers": {
    "chart-scanner": {
      "command": "chart-scanner-server",
      "args": ["--transport", "stdio"]
    }
  }
}
```

### Using Docker

```bash
docker pull <registry>/mcp-chart-scanner:latest
```

## Usage

### CLI Usage

```bash
chart-scanner <path-to-chart> [-f values.yaml] [--json] [--quiet]
```

### MCP Server Usage

#### Starting the server with stdio protocol

```bash
chart-scanner-server --transport stdio
```



## 버전 관리

이 프로젝트는 시맨틱 버전 관리를 사용합니다. 자세한 내용은 [버전 관리 가이드](./docs/versioning.md)를 참조하세요.

## Documentation

Complete documentation can be found in the [docs](./docs) directory.

## License

MIT
