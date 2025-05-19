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



## 버전 관리

이 프로젝트는 시맨틱 버전 관리를 사용합니다. 자세한 내용은 [버전 관리 가이드](./docs/versioning.md)를 참조하세요.

## Documentation

Complete documentation can be found in the [docs](./docs) directory.

## License

MIT
