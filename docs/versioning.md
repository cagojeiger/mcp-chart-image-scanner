# 버전 관리 가이드

## 자동 버전 관리

mcp-chart-image-scanner 저장소는 자동 버전 관리 시스템을 사용합니다. `main` 브랜치에 코드 변경이 푸시되면 GitHub Actions 워크플로우가 실행되어 자동으로 패치 버전을 증가시킵니다.

## 수동 버전 관리

특정 상황에서는 버전을 수동으로 관리해야 할 수 있습니다. 다음은 수동으로 버전을 관리하는 방법입니다.

### 패치 버전 증가 (예: 0.1.0 -> 0.1.1)

패치 버전은 버그 수정이나 작은 기능 변경에 사용됩니다.

1. `pyproject.toml` 파일을 엽니다:
   ```bash
   nano pyproject.toml
   ```

2. 버전 필드를 찾아 패치 버전을 증가시킵니다:
   ```toml
   version = "0.1.1"  # 0.1.0에서 증가
   ```

3. 변경 사항을 커밋하고 푸시합니다:
   ```bash
   git add pyproject.toml
   git commit -m "chore(release): bump version 0.1.0 → 0.1.1"
   git push
   ```

### 마이너 버전 증가 (예: 0.1.0 -> 0.2.0)

마이너 버전은 새로운 기능이 추가되었지만 이전 버전과 호환성이 유지될 때 사용됩니다.

1. `pyproject.toml` 파일을 엽니다:
   ```bash
   nano pyproject.toml
   ```

2. 버전 필드를 찾아 마이너 버전을 증가시키고 패치 버전을 0으로 재설정합니다:
   ```toml
   version = "0.2.0"  # 0.1.x에서 증가
   ```

3. 변경 사항을 커밋하고 푸시합니다:
   ```bash
   git add pyproject.toml
   git commit -m "chore(release): bump version 0.1.x → 0.2.0"
   git push
   ```

### 메이저 버전 증가 (예: 0.1.0 -> 1.0.0)

메이저 버전은 이전 버전과 호환되지 않는 변경 사항이 있을 때 사용됩니다.

1. `pyproject.toml` 파일을 엽니다:
   ```bash
   nano pyproject.toml
   ```

2. 버전 필드를 찾아 메이저 버전을 증가시키고 마이너 및 패치 버전을 0으로 재설정합니다:
   ```toml
   version = "1.0.0"  # 0.x.y에서 증가
   ```

3. 변경 사항을 커밋하고 푸시합니다:
   ```bash
   git add pyproject.toml
   git commit -m "chore(release): bump version 0.x.y → 1.0.0"
   git push
   ```

## 수동 릴리스 생성

GitHub 릴리스를 수동으로 생성하려면:

1. GitHub 저장소 페이지로 이동합니다.
2. "Releases" 탭을 클릭합니다.
3. "Draft a new release" 버튼을 클릭합니다.
4. 태그 버전을 입력합니다 (예: "v0.1.1").
5. 릴리스 제목을 입력합니다 (예: "v0.1.1").
6. 릴리스 노트를 작성합니다.
7. "Publish release" 버튼을 클릭합니다.
