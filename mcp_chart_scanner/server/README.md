# MCP Chart Image Scanner 서버

이 모듈은 MCP(Model Context Protocol) 서버 구현을 제공하여 Helm 차트에서 Docker 이미지를 추출합니다.

## 주요 기능

- `scan_chart_path`: 로컬 Helm 차트에서 Docker 이미지 스캔
- `scan_chart_url`: URL에서 Helm 차트 다운로드 및 스캔
- `scan_chart_upload`: 업로드된 Helm 차트 스캔

## 에러 처리 기능

- 파일 존재 여부 검증
- URL 다운로드 오류 처리
- 업로드된 차트 데이터 검증
- Helm CLI 존재 확인

## 호환성

- Cursor 호환: stdio 및 SSE 프로토콜 지원
- Smithery.ai 호환: Docker 패키징, stdio 및 SSE 프로토콜 지원

## 사용 예제

```python
from fastmcp import Client

async def main():
    async with Client("chart-scanner-server") as client:
        result = await client.call_tool(
            "scan_chart_path",
            {
                "path": "/path/to/chart.tgz",
                "normalize": True,
            },
        )
        print(result.text)
```
