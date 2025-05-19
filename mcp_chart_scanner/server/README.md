# MCP Chart Image Scanner 서버

이 모듈은 MCP(Model Context Protocol) 서버 구현을 제공하여 Helm 차트에서 Docker 이미지를 추출합니다.

## 주요 기능

- `scan_chart_path`: 로컬 Helm 차트에서 Docker 이미지 스캔 (절대 경로 필요)
- `scan_chart_url`: URL에서 Helm 차트 다운로드 및 스캔

## 에러 처리 기능

- 파일 존재 여부 검증
- URL 다운로드 오류 처리

- Helm CLI 존재 확인
- 경로 처리: 모든 경로는 절대 경로를 사용해야 함

## 호환성

- Cursor 호환: stdio 프로토콜 지원
- 알려진 문제: Cursor에서 INFO 로그가 [error] 태그로 표시됨

## 사용 예제

```python
from fastmcp import Client

async def main():
    async with Client("chart-scanner-server") as client:
        result = await client.call_tool(
            "scan_chart_path",
            {
                "path": "/path/to/chart.tgz",  # 절대 경로 사용
                "normalize": True,
            },
        )
        print(result.text)
```
