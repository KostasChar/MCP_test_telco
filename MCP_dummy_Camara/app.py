import logging
from fastmcp import FastMCP
from MCP_dummy_Camara.tools.qod import create_qod_session, get_qod_session, delete_qod_session, list_qod_sessions
from MCP_dummy_Camara.tools.edge_application import get_app_definitions
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MCP server")

app = FastMCP("MCP Server")
load_dotenv()

# Register tools - only audited functions are exposed — no wildcard imports or dynamic inclusion.
SAFE_TOOLS = [create_qod_session, get_qod_session, delete_qod_session, get_app_definitions, list_qod_sessions]

for tool in SAFE_TOOLS:
    app.tool()(tool)

if __name__ == "__main__":
    logger.info("Starting MCP Server (proxy mode)...")
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8000"))
    try:
        # default IP:127.0.0.1 and port 8000
        app.run(transport="streamable-http", host=host, port=port)
    except Exception as e:
        logger.critical("MCP server crashed: %s", e, exc_info=True)
