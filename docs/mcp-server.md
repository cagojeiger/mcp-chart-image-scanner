# MCP 서버 사용 가이드

이 문서는 Chart Image Scanner의 MCP(Model Context Protocol) 서버 사용 방법을 설명합니다.

## 기능 개요

MCP 서버는 Helm 차트에서 Docker 이미지를 추출하는 도구를 MCP 프로토콜을 통해 제공합니다. 다음 기능을 지원합니다:

- 로컬 Helm 차트 파일(.tgz) 또는 디렉토리에서 이미지 추출
- URL에서 Helm 차트 다운로드 및 이미지 추출

## 오류 처리 기능

서버는 다양한 오류 상황을 처리하고 상세한 오류 메시지를 제공합니다:

- 파일 존재 여부 검증: 지정된 경로에 차트 파일이 존재하지 않는 경우
- URL 형식 검증: URL이 http:// 또는 https://로 시작하지 않는 경우
- URL 다운로드 오류: 네트워크 연결 실패, 서버 응답 오류 등

- 차트 형식 검증: Chart.yaml 파일이 없는 경우, 유효하지 않은 tarball 형식 등
- Helm CLI 검증: Helm CLI가 설치되어 있지 않은 경우
- 임시 파일 관리: 임시 파일 생성 및 작업 완료 후 자동 정리
설치 방법은 [설치 가이드](./installation.md)를 참조하세요.

## 서버 시작하기

### stdio 프로토콜
```bash
chart-scanner-server --transport stdio
```

## 옵션

- `--transport`: 전송 프로토콜 (stdio만 지원)
- `-q, --quiet`: 로그 메시지 숨기기

## 사용 가능한 도구

### `scan_chart_path`

로컬 Helm 차트에서 Docker 이미지를 스캔합니다.

```python
async def scan_chart_path(
    path: str,  # 절대 경로를 사용해야 함
    values_files: Optional[List[str]] = None,  # 절대 경로를 사용해야 함
    normalize: bool = True,
) -> List[str]:
    """로컬 Helm 차트에서 Docker 이미지를 스캔합니다."""
```

### `scan_chart_url`

URL에서 Helm 차트를 스캔합니다.

```python
async def scan_chart_url(
    url: str,
    values_files: Optional[List[str]] = None,  # 절대 경로를 사용해야 함
    normalize: bool = True,
    timeout: int = 30,
) -> List[str]:
    """URL에서 Helm 차트를 스캔합니다."""
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
