# Cursor 호환성

MCP Chart Image Scanner는 [Cursor](https://cursor.com/) AI 코딩 도구와 호환됩니다.

## 요구사항

- MCP 서버는 stdio 프로토콜을 지원해야 합니다.
- MCP 서버는 SSE 프로토콜을 지원해야 합니다.
- MCP 서버는 표준 MCP 프로토콜을 준수해야 합니다.

## Cursor에서 사용하기

### stdio 프로토콜 사용

Cursor는 stdio 프로토콜을 통해 MCP 서버와 통신할 수 있습니다. 이 방식은 Cursor가 MCP 서버를 직접 실행하고 표준 입출력을 통해 통신하는 방식입니다.

```bash
chart-scanner-server --transport stdio
```

### SSE 프로토콜 사용

Cursor는 SSE(Server-Sent Events) 프로토콜을 통해 MCP 서버와 통신할 수 있습니다. 이 방식은 Cursor가 HTTP를 통해 MCP 서버에 연결하는 방식입니다.

```bash
chart-scanner-server --transport sse --host 0.0.0.0 --port 8000
```

## Cursor 설정

Cursor에서 MCP 서버를 설정하는 방법:

1. Cursor 설정 열기
2. "Model Context Protocol" 섹션으로 이동
3. 새 MCP 서버 추가
4. 서버 유형 선택 (stdio 또는 SSE)
5. 서버 정보 입력 (명령어 또는 URL)

## 예제

### stdio 예제

```json
{
  "name": "Chart Image Scanner",
  "transport": "stdio",
  "command": "chart-scanner-server --transport stdio"
}
```

### SSE 예제

```json
{
  "name": "Chart Image Scanner",
  "transport": "sse",
  "url": "http://localhost:8000/sse"
}
```

## 문제 해결

- **연결 오류**: Cursor가 MCP 서버에 연결할 수 없는 경우, 서버가 실행 중인지 확인하고 방화벽 설정을 확인하세요.
- **명령 오류**: 명령이 실행되지 않는 경우, 패키지가 올바르게 설치되었는지 확인하세요.
- **권한 오류**: 파일 접근 권한 오류가 발생하는 경우, 적절한 권한이 설정되어 있는지 확인하세요.
