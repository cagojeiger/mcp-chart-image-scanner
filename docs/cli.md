# 명령줄 인터페이스 (CLI)

MCP Chart Image Scanner는 Helm 차트에서 Docker 이미지를 추출하기 위한 명령줄 인터페이스를 제공합니다.

설치 방법은 [설치 가이드](./installation.md)를 참조하세요.


## 사용법

```bash
chart-scanner <차트-경로> [-f values.yaml] [--json] [--quiet] [--raw]
```

## 옵션

- `<차트-경로>`: .tgz Helm 차트 아카이브 또는 압축 해제된 차트 디렉토리 경로
- `-f, --values`: 추가 values.yaml 파일(들) (여러 번 지정 가능)
- `-q, --quiet`: 로그 메시지 숨기기 (stderr)
- `--json`: JSON 배열로 출력
- `--raw`: 정규화 없이 원시 이미지 이름 출력

## 예제

### 차트 아카이브에서 이미지 추출

```bash
chart-scanner /path/to/chart.tgz
```

### 차트 디렉토리에서 이미지 추출

```bash
chart-scanner /path/to/chart-directory
```

### 사용자 정의 values 파일로 이미지 추출

```bash
chart-scanner /path/to/chart.tgz -f values-prod.yaml -f values-secrets.yaml
```

### JSON으로 출력

```bash
chart-scanner /path/to/chart.tgz --json
```

### 로그 메시지 숨기기

```bash
chart-scanner /path/to/chart.tgz --quiet
```

### 정규화 없이 원시 이미지 이름 출력

```bash
chart-scanner /path/to/chart.tgz --raw
```
