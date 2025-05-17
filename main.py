from mcp_server import app, run_mcp_server
import uvicorn
import threading
import asyncio
import logging

logger = logging.getLogger(__name__)

def start_mcp_server_thread():
    """
    별도의 스레드에서 MCP 서버를 실행합니다.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_mcp_server())

if __name__ == "__main__":
    logging.info("Starting Helm Chart Image Scanner servers...")
    
    mcp_thread = threading.Thread(target=start_mcp_server_thread)
    mcp_thread.daemon = True
    mcp_thread.start()
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
