# Quick Start

이 문서는 MCP Chart Image Scanner를 빠르게 사용하기 위한 기본 예제를 제공합니다.

## 설치 요약

```bash
git clone https://github.com/cagojeiger/mcp-chart-image-scanner.git
cd mcp-chart-image-scanner
pipx install -e .
```

> **필수**: Helm CLI는 별도로 설치해야 합니다.

## CLI 사용 예시

아래 명령은 Helm 차트에서 이미지를 추출하여 JSON 배열로 출력합니다.

```bash
chart-scanner /path/to/chart.tgz -f values.yaml --json
```

## MCP 서버 기동

stdio 프로토콜을 사용해 MCP 서버를 실행하려면 다음 명령을 실행합니다.

```bash
chart-scanner-server --transport stdio
```
