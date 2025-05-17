import tempfile
import os
import sys
import shutil
import logging
import click
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import mcp.types as types
from mcp.server.lowlevel import Server
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from extract_docker_images import prepare_chart, helm_dependency_update, helm_template, collect_images

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Helm Chart Image Scanner API")

mcp_server = Server("helm-chart-image-scanner")

def extract_images_from_path(chart_path: str, values_files: Optional[List[str]] = None) -> List[str]:
    """
    Helm 차트 경로에서 Docker 이미지 목록을 추출합니다.
    
    Args:
        chart_path: Helm 차트 경로 (.tgz 파일 또는 디렉토리)
        values_files: 추가 values 파일 경로 목록 (선택적)
        
    Returns:
        추출된 Docker 이미지 목록
    """
    try:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            
            chart_root = prepare_chart(Path(chart_path), workdir)
            
            values_paths = [Path(vf) for vf in (values_files or [])]
            
            helm_dependency_update(chart_root)
            rendered = helm_template(chart_root, values_paths)
            
            images = collect_images(rendered)
            return images
    except Exception as e:
        logger.error(f"차트 경로 처리 중 오류: {str(e)}")
        return [f"Error: {str(e)}"]

async def extract_images_from_upload(chart_data: bytes, values_files: Optional[Dict[str, bytes]] = None) -> List[str]:
    """
    업로드된 Helm 차트 데이터에서 Docker 이미지 목록을 추출합니다.
    
    Args:
        chart_data: 업로드된 차트 파일 데이터 (.tgz 형식)
        values_files: 파일명과 데이터로 구성된 추가 values 파일 딕셔너리 (선택적)
        
    Returns:
        추출된 Docker 이미지 목록
    """
    try:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            
            chart_file = workdir / "chart.tgz"
            with open(chart_file, "wb") as f:
                f.write(chart_data)
            
            values_paths = []
            if values_files:
                for filename, content in values_files.items():
                    values_path = workdir / filename
                    with open(values_path, "wb") as f:
                        f.write(content)
                    values_paths.append(values_path)
            
            chart_root = prepare_chart(chart_file, workdir)
            
            helm_dependency_update(chart_root)
            rendered = helm_template(chart_root, values_paths)
            
            images = collect_images(rendered)
            return images
    except Exception as e:
        logger.error(f"업로드된 차트 처리 중 오류: {str(e)}")
        return [f"Error: {str(e)}"]

@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """
    MCP 도구 호출 처리
    """
    if name == "extract_from_path":
        if "chart_path" not in arguments:
            raise ValueError("Missing required argument 'chart_path'")
        
        chart_path = arguments["chart_path"]
        values_files = arguments.get("values_files", [])
        
        images = extract_images_from_path(chart_path, values_files)
        return [types.TextContent(type="text", text="\n".join(images))]
    
    elif name == "extract_from_upload":
        if "chart_data" not in arguments:
            raise ValueError("Missing required argument 'chart_data'")
        
        chart_data = arguments["chart_data"]
        values_files = arguments.get("values_files", {})
        
        images = await extract_images_from_upload(chart_data, values_files)
        return [types.TextContent(type="text", text="\n".join(images))]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

@mcp_server.list_tools()
async def list_tools() -> List[types.Tool]:
    """
    사용 가능한 MCP 도구 목록 반환
    """
    return [
        types.Tool(
            name="extract_from_path",
            description="Helm 차트 경로에서 Docker 이미지 목록을 추출합니다",
            inputSchema={
                "type": "object",
                "required": ["chart_path"],
                "properties": {
                    "chart_path": {
                        "type": "string",
                        "description": "Helm 차트 경로 (.tgz 파일 또는 디렉토리)",
                    },
                    "values_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "추가 values 파일 경로 목록 (선택적)",
                    },
                },
            },
        ),
        types.Tool(
            name="extract_from_upload",
            description="업로드된 Helm 차트 데이터에서 Docker 이미지 목록을 추출합니다",
            inputSchema={
                "type": "object",
                "required": ["chart_data"],
                "properties": {
                    "chart_data": {
                        "type": "string",
                        "format": "binary",
                        "description": "업로드된 차트 파일 데이터 (.tgz 형식)",
                    },
                    "values_files": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "string",
                            "format": "binary",
                        },
                        "description": "파일명과 데이터로 구성된 추가 values 파일 딕셔너리 (선택적)",
                    },
                },
            },
        ),
    ]

@app.post("/upload/", response_model=List[str])
async def upload_chart(
    chart_file: UploadFile = File(...),
    values_files: List[UploadFile] = File([])
):
    """
    Helm 차트 파일을 업로드하여 Docker 이미지 목록을 추출합니다.
    """
    try:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            
            chart_path = workdir / chart_file.filename
            with open(chart_path, "wb") as f:
                shutil.copyfileobj(chart_file.file, f)
            
            values_paths = []
            for vf in values_files:
                values_path = workdir / vf.filename
                with open(values_path, "wb") as f:
                    shutil.copyfileobj(vf.file, f)
                values_paths.append(values_path)
            
            chart_root = prepare_chart(chart_path, workdir)
            
            helm_dependency_update(chart_root)
            rendered = helm_template(chart_root, values_paths)
            
            images = collect_images(rendered)
            return images
    except Exception as e:
        logger.error(f"API 업로드 처리 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {"status": "healthy", "service": "mcp-chart-image-scanner"}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Helm Chart Image Scanner MCP server...")

if __name__ == "__main__":
    import uvicorn
    import anyio
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
