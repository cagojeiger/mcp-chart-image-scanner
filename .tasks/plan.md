# MCP Chart Image Scanner 개발 계획

## 완료된 작업

### 1. 기본 구조 구현
- pip 설치 패키지 구조 생성 (pyproject.toml, 패키지 디렉토리 등)
- 기본 .gitignore 파일 추가
- 문서화 디렉토리 구조 생성 (docs/)

### 2. 핵심 기능 구현
- extract_docker_images.py 스크립트를 모듈화하여 extract.py로 변환
- CLI 도구 구현 (mcp_chart_scanner/cli.py)
- MCP 서버 구현 (mcp_chart_scanner/server/mcp_server.py)
- Helm CLI 존재 확인 기능 추가

### 3. CI/CD 파이프라인 구현
- GitHub Actions 워크플로우 구현 (lint, test, build, docker)
- 자동 버전 증가 워크플로우 구현
- 릴리즈 드래프터 설정
- 커밋 컨벤션 검증 기능 추가

### 4. 문서화
- 기본 README.md 업데이트
- CLI 사용 가이드 작성
- MCP 서버 사용 가이드 작성
- Docker 이미지 사용 가이드 작성
- 버전 관리 문서 작성

### 5. 파일 처리 기능 개선
- 테스트 실패 이슈 해결:
  - scan_chart_path: FileNotFoundError와 ValueError 간의 불일치 해결
  - scan_chart_url: requests.get 호출 시 timeout 매개변수 불일치 해결
  - scan_chart_upload: mock_temp_file.write 호출 문제 해결
  - test_scan_chart_url_request_exception: 이중 오류 로깅 문제 해결

- 개선된 기능:
  - 로컬 차트 경로 검증 강화 (Chart.yaml 존재 여부 확인)
  - URL 다운로드 처리 개선 (URL 형식 검증, 타임아웃 매개변수화, 진행상황 로깅)
  - 업로드된 차트 데이터 검증 강화 (크기 제한, 차트 형식 검증)
  - 임시 파일 관리 개선 (작업 완료 후 정리 및 로깅)
  - 일관된 오류 처리 패턴 적용

## 진행 중인 작업

### 1. Cursor 호환성 개선
- SSE 모드 제거 및 stdio 모드로 일원화
- scan_chart_upload 도구 제거
- 절대 경로 요구사항 명시
- Cursor 로깅 관련 알려진 문제 문서화
- Docker 빌드 기능 제거

## 향후 계획

### 1. 호환성 테스트 강화
- Cursor 호환성 테스트 추가
- Smithery.ai 호환성 테스트 추가
- 다양한 Helm 차트 형식에 대한 테스트 추가

### 2. 성능 최적화
- 대용량 차트 처리 성능 개선
- 메모리 사용량 최적화
- 병렬 처리 가능성 검토

### 3. 추가 기능 구현
- 이미지 취약점 스캔 기능 추가 검토
- 차트 의존성 분석 기능 추가 검토
- 이미지 태그 정책 검증 기능 추가 검토

## 구현 우선순위

1. 호환성 테스트 강화
2. 성능 최적화
3. 추가 기능 구현
