# MCP Chart Image Scanner

A tool for extracting Docker image references from Helm charts with CLI and MCP server support.

## Features

- Extract Docker image references from Helm charts (.tgz archives or directories)
- Command Line Interface (CLI) for local usage
- Model Context Protocol (MCP) server for integration with AI tools
- Support for multiple input methods:
  - Local file paths
  - Remote URLs
- Support for stdio communication protocol
자세한 설치 방법은 [설치 가이드](./docs/installation.md)를 참조하세요.

## 설치

아래 절차에 따라 프로젝트를 설치합니다.

1. 저장소를 클론합니다.
   ```bash
   git clone https://github.com/cagojeiger/mcp-chart-image-scanner.git
   cd mcp-chart-image-scanner
   ```
2. `pipx`를 사용해 설치하거나 가상 환경을 만듭니다.
   ```bash
   pipx install -e .
   ```
   가상 환경 사용 시:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -e .
   ```
3. Helm CLI를 별도로 설치해야 합니다.
4. 커밋 전에 코드 검사를 실행하려면 `pre-commit`을 설치합니다.
   ```bash
   pip install pre-commit
   pre-commit install
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



## Documentation

For a brief introduction, see the [Quick Start guide](./docs/quickstart.md).
Complete documentation can be found in the [documentation index](./docs/README.md).

## License

MIT
