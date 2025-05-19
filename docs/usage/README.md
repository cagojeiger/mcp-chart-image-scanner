# 사용 설명서

이 디렉토리는 MCP Chart Image Scanner의 사용 예제와 튜토리얼을 포함합니다.

## 기본 사용법

### CLI 사용법

```bash
# 차트에서 이미지 추출
chart-scanner /path/to/chart.tgz

# 사용자 정의 values 파일로 이미지 추출
chart-scanner /path/to/chart.tgz -f values-prod.yaml

# JSON으로 출력
chart-scanner /path/to/chart.tgz --json
```

### Python API 사용법

```python
from mcp_chart_scanner.extract import extract_images_from_chart

# 차트에서 이미지 추출
images = extract_images_from_chart(
    chart_path="/path/to/chart.tgz",
    values_files=["/path/to/values.yaml"],
    normalize=True,
)

# 이미지 출력
for image in images:
    print(image)
```

### MCP 서버 사용법

```bash
# stdio 프로토콜로 서버 시작
chart-scanner-server --transport stdio
```

## 고급 사용법

더 많은 예제는 [고급 사용 가이드](./advanced.md)를 참조하세요.
