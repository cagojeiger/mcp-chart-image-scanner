# mcp-chart-image-scanner

Helm 차트(+옵션 values 파일) 경로 또는 직접 파일 업로드를 받아 사용되는 Docker 이미지 목록을 출력하는 MCP 서버

## 요구사항

- Python 3.8 이상
- Helm CLI (이미지 추출 기능에 필요)

## 설치 및 실행

### Docker 사용 (권장)

```bash
# 도커 이미지 빌드
docker build -t mcp-chart-image-scanner .

# 도커 컨테이너 실행
docker run -p 8000:8000 mcp-chart-image-scanner
```

### 로컬 설치

```bash
# pip 사용
pip install -e .

# 또는 uv 사용 (권장)
uv pip install -e .

# 서버 실행
python main.py
```

## 사용 방법

### MCP 서버 기능

서버는 두 가지 방식으로 사용할 수 있습니다:

1. **MCP 프로토콜**: MCP 호환 클라이언트를 통한 접근
2. **REST API**: 직접 HTTP 요청을 통한 접근

### REST API 엔드포인트

- `POST /upload/`: Helm 차트 파일 업로드를 통한 이미지 목록 추출

### Cursor 또는 기타 MCP 호환 도구에 등록

```json
{
  "mcpServers": {
    "helm-chart-image-scanner": {
      "command": "docker",
      "args": ["run", "-p", "8000:8000", "mcp-chart-image-scanner"]
    }
  }
}
```

## 기능

- `extract_images_from_path`: Helm 차트 경로를 통해 이미지 목록 추출
- `extract_images_from_upload`: 업로드된 Helm 차트 파일을 통해 이미지 목록 추출

## Smithery.ai 마켓플레이스 호환성

이 MCP 서버는 [Smithery.ai](https://smithery.ai) 마켓플레이스와 호환됩니다. 마켓플레이스에 등록하려면 서버를 공개적으로 접근 가능한 URL에 배포하고 해당 URL을 등록하세요.
