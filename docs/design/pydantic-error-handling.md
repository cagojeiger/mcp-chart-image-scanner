# Pydantic 기반 에러 처리 및 유효성 검증 시스템 설계

## 현재 에러 처리 시스템

현재 MCP 서버는 다음과 같은 방식으로 에러를 처리하고 있습니다:

1. **문자열 상수 기반 에러 메시지**:
   ```python
   ERROR_CHART_NOT_FOUND = "Chart path not found: {path}"
   ERROR_CHART_INVALID = "Invalid chart format: {error}"
   ERROR_FILE_NOT_FOUND = "File not found: {error}"
   ERROR_DOWNLOAD_FAILED = "Failed to download chart: {error}"
   ERROR_EMPTY_UPLOAD = "Empty chart data received"
   ERROR_GENERAL = "Error processing chart: {error}"
   ```

2. **log_and_raise 유틸리티 함수**:
   ```python
   async def log_and_raise(
       error_msg: str, ctx: Optional[Context] = None, exception_type=Exception
   ) -> None:
       if ctx:
           await ctx.error(error_msg)
       raise exception_type(error_msg)
   ```

3. **try-except 블록 내에서 에러 처리**:
   ```python
   try:
       # 작업 수행
   except FileNotFoundError as e:
       error_msg = ERROR_FILE_NOT_FOUND.format(error=str(e))
       await log_and_raise(error_msg, ctx, FileNotFoundError)
   except Exception as e:
       error_msg = ERROR_GENERAL.format(error=str(e))
       await log_and_raise(error_msg, ctx, ValueError)
   ```

이 방식은 간단하고 직관적이지만, 다음과 같은 제한사항이 있습니다:

- 에러 정보가 단순 문자열로 제한됨
- 구조화된 에러 데이터를 제공하기 어려움
- 일관된 에러 형식을 강제하기 어려움
- 클라이언트에서 에러 처리가 어려움 (문자열 파싱 필요)

## 제안하는 Pydantic 기반 에러 처리 시스템

Pydantic을 활용하여 다음과 같은 구조화된 에러 처리 시스템을 구현할 수 있습니다:

1. **기본 에러 모델 정의**:
   ```python
   from pydantic import BaseModel, Field
   from typing import Optional, Dict, Any, List
   
   class ErrorDetail(BaseModel):
       """에러 세부 정보 모델."""
       loc: Optional[List[str]] = None  # 에러 발생 위치 (경로, 필드 등)
       msg: str  # 에러 메시지
       type: str  # 에러 유형 (예: value_error, type_error 등)
   
   class ErrorModel(BaseModel):
       """기본 에러 모델."""
       code: str  # 에러 코드 (예: chart_not_found, invalid_format 등)
       message: str  # 사용자 친화적인 에러 메시지
       details: Optional[List[ErrorDetail]] = None  # 상세 에러 정보
   ```

2. **에러 유형별 서브클래스 생성**:
   ```python
   class ChartNotFoundError(ErrorModel):
       """차트를 찾을 수 없을 때 발생하는 에러."""
       code: str = "chart_not_found"
       
   class InvalidChartError(ErrorModel):
       """유효하지 않은 차트 형식일 때 발생하는 에러."""
       code: str = "invalid_chart_format"
       
   class DownloadFailedError(ErrorModel):
       """차트 다운로드 실패 시 발생하는 에러."""
       code: str = "download_failed"
   ```

3. **에러 핸들러 함수 구현**:
   ```python
   async def raise_error(
       error: ErrorModel, ctx: Optional[Context] = None, exception_type=Exception
   ) -> None:
       """구조화된 에러 모델을 로깅하고 예외를 발생시킵니다.
       
       Args:
           error: 에러 모델 인스턴스
           ctx: MCP 컨텍스트
           exception_type: 발생시킬 예외 유형
       """
       if ctx:
           await ctx.error(error.model_dump_json())
       raise exception_type(error.message)
   ```

4. **유효성 검증 모델 정의**:
   ```python
   class ChartPath(BaseModel):
       """차트 경로 유효성 검증 모델."""
       path: str
       values_files: Optional[List[str]] = None
       
       @validator("path")
       def validate_path_exists(cls, v):
           if not os.path.exists(v):
               raise ValueError(f"Chart path not found: {v}")
           return v
   
   class ChartURL(BaseModel):
       """차트 URL 유효성 검증 모델."""
       url: str
       values_files: Optional[List[str]] = None
       
       @validator("url")
       def validate_url_format(cls, v):
           if not v.startswith(("http://", "https://")):
               raise ValueError(f"Invalid URL format: {v}")
           return v
   
   class ChartUpload(BaseModel):
       """업로드된 차트 데이터 유효성 검증 모델."""
       chart_data: bytes
       values_files: Optional[List[str]] = None
       
       @validator("chart_data")
       def validate_chart_data(cls, v):
           if not v:
               raise ValueError("Empty chart data received")
           if len(v) > 50 * 1024 * 1024:  # 50MB
               raise ValueError(f"Chart too large: {len(v) / (1024 * 1024):.2f}MB (max 50MB)")
           return v
   ```

## 구현 방안

1. **MCP 도구 함수 수정**:
   ```python
   @mcp.tool()
   async def scan_chart_path(
       path: str,
       values_files: Optional[List[str]] = None,
       normalize: bool = True,
       ctx: Context = None,
   ) -> List[str]:
       """로컬 Helm 차트에서 Docker 이미지를 스캔합니다."""
       if ctx:
           await ctx.info(f"Scanning chart at path: {path}")
       
       try:
           # Pydantic 모델을 사용한 유효성 검증
           validated_input = ChartPath(path=path, values_files=values_files)
           
           # 차트 유효성 검증 (Chart.yaml 존재 여부 등)
           if os.path.isdir(validated_input.path) and not os.path.exists(os.path.join(validated_input.path, "Chart.yaml")):
               error = InvalidChartError(
                   message="Not a valid Helm chart directory (Chart.yaml not found)",
                   details=[
                       ErrorDetail(
                           loc=["path"],
                           msg="Chart.yaml not found in directory",
                           type="value_error.chart.invalid"
                       )
                   ]
               )
               await raise_error(error, ctx, ValueError)
           
           # 이미지 추출
           images = extract_images_from_chart(
               chart_path=validated_input.path,
               values_files=validated_input.values_files,
               normalize=normalize,
           )
           
           if ctx:
               await ctx.info(f"Found {len(images)} images")
           
           return images
       except ValueError as e:
           if "Chart path not found" in str(e):
               error = ChartNotFoundError(
                   message=str(e),
                   details=[
                       ErrorDetail(
                           loc=["path"],
                           msg=str(e),
                           type="value_error.path.not_found"
                       )
                   ]
               )
               await raise_error(error, ctx, FileNotFoundError)
           else:
               error = InvalidChartError(
                   message=str(e),
                   details=[
                       ErrorDetail(
                           loc=["path"],
                           msg=str(e),
                           type="value_error.chart.invalid"
                       )
                   ]
               )
               await raise_error(error, ctx, ValueError)
       except Exception as e:
           error = ErrorModel(
               code="general_error",
               message=f"Error processing chart: {str(e)}",
               details=[
                   ErrorDetail(
                       msg=str(e),
                       type="error.general"
                   )
               ]
           )
           await raise_error(error, ctx, ValueError)
   ```

2. **에러 응답 형식**:
   ```json
   {
     "code": "invalid_chart_format",
     "message": "Not a valid Helm chart directory (Chart.yaml not found)",
     "details": [
       {
         "loc": ["path"],
         "msg": "Chart.yaml not found in directory",
         "type": "value_error.chart.invalid"
       }
     ]
   }
   ```

## 장점

1. **구조화된 에러 정보**:
   - 에러 코드, 메시지, 상세 정보를 구조화된 형식으로 제공
   - 클라이언트에서 쉽게 파싱하고 처리 가능

2. **자동 유효성 검증**:
   - Pydantic 모델을 통한 입력 데이터 자동 검증
   - 타입 변환 및 검증 로직 통합

3. **일관된 에러 처리**:
   - 모든 에러가 동일한 형식으로 처리됨
   - 에러 처리 로직 중앙화

4. **문서화 및 스키마 자동 생성**:
   - Pydantic 모델을 통한 API 스키마 자동 생성
   - 클라이언트에 에러 형식 문서 제공 용이

5. **확장성**:
   - 새로운 에러 유형 쉽게 추가 가능
   - 에러 처리 로직 분리로 유지보수 용이

## 구현 계획

1. **에러 모델 정의**:
   - `mcp_chart_scanner/server/errors.py` 파일 생성
   - 기본 에러 모델 및 서브클래스 구현

2. **유효성 검증 모델 정의**:
   - `mcp_chart_scanner/server/validators.py` 파일 생성
   - 입력 데이터 유효성 검증 모델 구현

3. **MCP 서버 리팩토링**:
   - 기존 문자열 상수 기반 에러 처리를 Pydantic 모델로 대체
   - 에러 핸들러 함수 업데이트

4. **테스트 업데이트**:
   - 새로운 에러 처리 시스템에 맞게 테스트 업데이트
   - 에러 모델 및 유효성 검증 모델 테스트 추가

## 결론

Pydantic 기반 에러 처리 및 유효성 검증 시스템은 MCP 서버의 에러 처리를 더 강력하고 일관되게 만들어 줍니다. 구조화된 에러 정보를 제공하여 클라이언트에서 더 쉽게 에러를 처리할 수 있게 하고, 자동 유효성 검증을 통해 코드의 안정성과 가독성을 향상시킵니다.

이 설계는 FastAPI의 에러 처리 패턴을 참고하여 작성되었으며, FastMCP와 함께 사용하기에 적합한 형태로 구성되었습니다.
