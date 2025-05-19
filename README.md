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



## Local Development

개발 의존성은 다음 명령으로 설치합니다.

```bash
make setup
```

## Documentation

For a brief introduction, see the [Quick Start guide](./docs/quickstart.md).
Complete documentation can be found in the [documentation index](./docs/README.md).

## License

MIT
