# Cursor 호환성

MCP Chart Image Scanner는 [Cursor](https://cursor.com/) AI 코딩 도구와 호환됩니다.

## 요구사항

- MCP 서버는 stdio 프로토콜을 지원해야 합니다.
- MCP 서버는 표준 MCP 프로토콜을 준수해야 합니다.

## Cursor에서 사용하기

Cursor는 MCP 서버를 직접 실행하여 stdio 프로토콜로 통신합니다. 설치가 완료되면 다음과 같이 `.cursor.json` 파일에 MCP 서버를 등록합니다.

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

### MCP 서버 수동 실행

서버를 직접 실행하려면 다음 명령을 사용할 수 있습니다.

```bash
chart-scanner-server --transport stdio
```

## 문제 해결

- **연결 오류**: Cursor가 MCP 서버에 연결할 수 없는 경우, 서버가 실행 중인지 확인하고 방화벽 설정을 확인하세요.
- **명령 오류**: 명령이 실행되지 않는 경우, 패키지가 올바르게 설치되었는지 확인하세요.
- **권한 오류**: 파일 접근 권한 오류가 발생하는 경우, 적절한 권한이 설정되어 있는지 확인하세요.
- **경로 오류**: 항상 절대 경로를 사용하세요. 상대 경로는 오류를 발생시킬 수 있습니다.
- **로깅 표시 오류**: Cursor에서 INFO 로그가 [error] 태그로 표시될 수 있습니다. 이는 알려진 문제이며 로그 내용에는 영향을 미치지 않습니다.
