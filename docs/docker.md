# Docker 이미지

MCP Chart Image Scanner는 MCP 서버를 실행하기 위한 Docker 이미지를 제공합니다.

## 특징

- Alpine 기반 이미지
- Helm CLI 포함
- stdio 및 SSE 프로토콜을 지원하는 MCP 서버

## 사용법

### 이미지 가져오기

```bash
docker pull <registry>/mcp-chart-scanner:latest
```

### SSE 프로토콜로 서버 실행

```bash
docker run -p 8000:8000 <registry>/mcp-chart-scanner:latest
```

### stdio 프로토콜로 서버 실행

```bash
docker run -i <registry>/mcp-chart-scanner:latest chart-scanner-server --transport stdio
```

### CLI 실행

```bash
docker run -v /path/to/charts:/charts <registry>/mcp-chart-scanner:latest chart-scanner /charts/mychart.tgz
```

## 이미지 빌드

```bash
docker build -t <registry>/mcp-chart-scanner:latest .
```

## 환경 변수

- `PYTHONUNBUFFERED`: 1로 설정하여 Python 출력이 버퍼링되지 않도록 합니다.

## 포트

- `8000`: SSE 프로토콜의 기본 포트
