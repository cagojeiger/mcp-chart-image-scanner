# 고급 사용법

이 문서는 MCP Chart Image Scanner의 고급 사용 예제를 제공합니다.


## 사용자 정의 클라이언트와 MCP 서버 사용하기

### Python 클라이언트

```python
from fastmcp import Client

async def main():
    # 서버에 연결 (stdio)
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

### JavaScript 클라이언트

```javascript
// JavaScript MCP 클라이언트 사용 예제
// (구현은 특정 클라이언트 라이브러리에 따라 다름)
```

## CI/CD 파이프라인과의 통합

### GitHub Actions 예제

```yaml
name: Helm 차트 스캔

on:
  push:
    paths:
      - 'charts/**'

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      
      - name: MCP Chart Scanner 설치
        run: |
          git clone https://github.com/cagojeiger/mcp-chart-image-scanner.git
          cd mcp-chart-image-scanner
          pipx install -e .
      
      - name: 차트 스캔
        run: |
          chart-scanner ./charts/mychart --json > images.json
      
      - name: 결과 업로드
        uses: actions/upload-artifact@v3
        with:
          name: images
          path: images.json
```

### GitLab CI 예제

```yaml
scan-chart:
  image: python:3.10-alpine
  script:
    - apk add --no-cache curl bash git
    - curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
    - chmod 700 get_helm.sh
    - ./get_helm.sh
    - git clone https://github.com/cagojeiger/mcp-chart-image-scanner.git
    - cd mcp-chart-image-scanner
    - pipx install -e .
    - chart-scanner ./charts/mychart --json > images.json
  artifacts:
    paths:
      - images.json
```
