# MCP 서버 사용 가이드

이 문서는 Chart Image Scanner의 MCP(Model Context Protocol) 서버 사용 방법을 설명합니다.

## 기능 개요

MCP 서버는 Helm 차트에서 Docker 이미지를 추출하는 도구를 MCP 프로토콜을 통해 제공합니다. 다음 기능을 지원합니다:

- 로컬 Helm 차트 파일(.tgz) 또는 디렉토리에서 이미지 추출
- URL에서 Helm 차트 다운로드 및 이미지 추출
- 업로드된 Helm 차트 데이터에서 이미지 추출

## 오류 처리 기능

서버는 다양한 오류 상황을 처리하고 상세한 오류 메시지를 제공합니다:

- 파일 존재 여부 검증: 지정된 경로에 차트 파일이 존재하지 않는 경우
- URL 형식 검증: URL이 http:// 또는 https://로 시작하지 않는 경우
- URL 다운로드 오류: 네트워크 연결 실패, 서버 응답 오류 등
- 업로드 데이터 검증: 빈 데이터, 크기 제한 초과(기본 10MB), 손상된 데이터 등
- 차트 형식 검증: Chart.yaml 파일이 없는 경우, 유효하지 않은 tarball 형식 등
- Helm CLI 검증: Helm CLI가 설치되어 있지 않은 경우
- 임시 파일 관리: 임시 파일 생성 및 작업 완료 후 자동 정리

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
    timeout: int = 30,
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
    max_size_mb: int = 10,
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
