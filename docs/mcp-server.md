# MCP 서버

MCP Chart Image Scanner는 Helm 차트에서 Docker 이미지를 추출하기 위한 Model Context Protocol(MCP) 서버를 제공합니다.

## 설치

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

## 서버 시작하기

### stdio 프로토콜

```bash
chart-scanner-server --transport stdio
```

### SSE 프로토콜

```bash
chart-scanner-server --transport sse --host 0.0.0.0 --port 8000 --path /sse
```

## 옵션

- `--transport`: 전송 프로토콜 (stdio 또는 sse)
- `--host`: 바인딩할 호스트 (sse 전송용)
- `--port`: 바인딩할 포트 (sse 전송용)
- `--path`: SSE 엔드포인트 경로 (sse 전송용)
- `-q, --quiet`: 로그 메시지 숨기기

## 사용 가능한 도구

### `scan_chart_path`

로컬 Helm 차트에서 Docker 이미지를 스캔합니다.

```python
async def scan_chart_path(
    path: str,
    values_files: Optional[List[str]] = None,
    normalize: bool = True,
) -> List[str]:
    """로컬 Helm 차트에서 Docker 이미지를 스캔합니다."""
```

### `scan_chart_url`

URL에서 Helm 차트를 스캔합니다.

```python
async def scan_chart_url(
    url: str,
    values_files: Optional[List[str]] = None,
    normalize: bool = True,
) -> List[str]:
    """URL에서 Helm 차트를 스캔합니다."""
```

### `scan_chart_upload`

업로드된 Helm 차트를 스캔합니다.

```python
async def scan_chart_upload(
    chart_data: bytes,
    values_files: Optional[List[str]] = None,
    normalize: bool = True,
) -> List[str]:
    """업로드된 Helm 차트를 스캔합니다."""
```

## 사용 가능한 리소스

### `help://usage`

사용 정보를 가져옵니다.

```python
def get_usage() -> str:
    """사용 정보를 가져옵니다."""
```

## Python 클라이언트 사용 예제

```python
from fastmcp import Client

async def main():
    # 서버에 연결
    async with Client("chart-scanner-server") as client:
        # 사용 가능한 도구 나열
        tools = await client.list_tools()
        print(f"사용 가능한 도구: {tools}")
        
        # 로컬 차트 스캔
        result = await client.call_tool(
            "scan_chart_path",
            {
                "path": "/path/to/chart.tgz",
                "values_files": ["/path/to/values.yaml"],
                "normalize": True,
            },
        )
        
        # 결과 출력
        print(f"이미지: {result.text}")
```

## Cursor와의 호환성

MCP 서버는 [Cursor](https://cursor.com/) AI 코딩 도구와 호환됩니다. 자세한 내용은 [Cursor 호환성 문서](./cursor.md)를 참조하세요.
