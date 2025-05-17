from mcp_server import app, mcp_server
import uvicorn
import asyncio
import logging

logger = logging.getLogger(__name__)

async def start_mcp_server():
    """
    MCP 서버와 FastAPI 앱을 함께 실행합니다.
    """
    mcp_task = asyncio.create_task(mcp_server.serve(host="0.0.0.0", port=8001))
    
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    
    await server.serve()
    
    await mcp_task

if __name__ == "__main__":
    logging.info("Starting Helm Chart Image Scanner servers...")
    asyncio.run(start_mcp_server())
