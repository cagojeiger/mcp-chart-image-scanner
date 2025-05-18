# API 문서

이 디렉토리는 MCP Chart Image Scanner의 Python API 문서를 포함합니다.

## 핵심 모듈

핵심 모듈은 Helm 차트에서 Docker 이미지를 추출하는 기능을 제공합니다.

### `extract_images_from_chart`

```python
def extract_images_from_chart(
    chart_path: Union[str, pathlib.Path],
    values_files: Optional[List[Union[str, pathlib.Path]]] = None,
    normalize: bool = True,
) -> List[str]:
    """Helm 차트에서 Docker 이미지를 추출합니다.

    Args:
        chart_path: .tgz 차트 아카이브 또는 차트 디렉토리 경로
        values_files: 추가 values 파일 목록
        normalize: 이미지 이름 정규화 여부

    Returns:
        정렬된 Docker 이미지 목록
    """
```

이 함수는 차트에서 이미지를 추출하는 모든 단계를 결합한 주요 함수입니다.

## 사용 예제

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
