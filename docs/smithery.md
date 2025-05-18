# Smithery.ai 마켓플레이스 호환성

MCP Chart Image Scanner는 Smithery.ai 마켓플레이스와 호환됩니다.

## 요구사항

- MCP 서버는 Docker 이미지로 패키징되어야 합니다.
- MCP 서버는 stdio 프로토콜을 지원해야 합니다.
- MCP 서버는 SSE 프로토콜을 지원해야 합니다.
- MCP 서버는 적절한 문서를 제공해야 합니다.

## 배포

### Docker 이미지 빌드

```bash
docker build -t <registry>/mcp-chart-scanner:latest .
```

### 레지스트리에 이미지 푸시

```bash
docker push <registry>/mcp-chart-scanner:latest
```

### Smithery.ai에 배포

Smithery.ai 문서를 따라 MCP 서버를 마켓플레이스에 배포하세요.

## MCP 서버 사양

### 이름

"Chart Image Scanner"

### 설명

"Helm 차트에서 Docker 이미지 참조 추출"

### 도구

- `scan_chart_path`: 로컬 Helm 차트에서 Docker 이미지 스캔
- `scan_chart_url`: URL에서 Helm 차트 스캔
- `scan_chart_upload`: 업로드된 Helm 차트 스캔

### 리소스

- `help://usage`: 사용 정보 가져오기

## 사용 예제

```python
# MCP 서버에 연결
async with Client("chart-scanner-server") as client:
    # URL에서 차트 스캔
    result = await client.call_tool(
        "scan_chart_url",
        {
            "url": "https://example.com/chart.tgz",
            "normalize": True,
        },
    )
    
    # 결과 출력
    print(f"이미지: {result.text}")
```
