# 설치 가이드

이 문서는 MCP Chart Image Scanner의 설치 방법을 설명합니다.

## 기본 설치

1. 저장소를 클론합니다.
   ```bash
   git clone https://github.com/cagojeiger/mcp-chart-image-scanner.git
   cd mcp-chart-image-scanner
   ```
2. `pipx`를 사용하여 설치합니다.
   ```bash
   pipx install -e .
   ```

   가상 환경을 이용하려면 다음과 같이 실행합니다.
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

### 필수 조건

- Helm CLI가 포함되어 있지 않으므로 별도로 설치해야 합니다.
- 반드시 프로젝트 루트 디렉토리(`mcp-chart-image-scanner/`)에서 설치해야 합니다.
- 일부 시스템에서 `externally-managed-environment` 오류가 발생할 경우 가상 환경을 생성하거나 `pip install -e . --break-system-packages` 옵션을 사용합니다.

## Cursor 연동

설치 후 Cursor에서 MCP 서버를 사용하려면 `.cursor.json` 파일에 다음과 같이 등록합니다.

```json
{
  "mcpServers": {
    "chart-scanner": {
      "command": "chart-scanner-server",
      "args": ["--transport", "stdio"]
    }
  }
}
```
