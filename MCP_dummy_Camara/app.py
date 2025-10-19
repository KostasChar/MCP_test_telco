import logging
from mcp.server.fastmcp import FastMCP
<<<<<<< Updated upstream:MCP_dummy_Camara/app.py
from MCP_dummy_Camara.tools.qod import create_qod_session, get_qod_session, delete_qod_session
=======
from MCPserver_2.tools.qod import create_qod_session, get_qod_session, delete_qod_session
from dotenv import load_dotenv
import os
>>>>>>> Stashed changes:MCPserver_2/app.py

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MCP server")

app = FastMCP("MCP Server")
load_dotenv()


# Register tools - only audited functions are exposed — no wildcard imports or dynamic inclusion.
SAFE_TOOLS = [create_qod_session, get_qod_session, delete_qod_session]


for tool in SAFE_TOOLS:
    app.tool()(tool)


if __name__ == "__main__":
    logger.info("Starting QoS MCP Server (proxy mode)...")
    try:
        # default IP:127.0.0.1 and port 8000
        app.run(transport="streamable-http")
    except Exception as e:
        logger.critical("MCP server crashed: %s", e, exc_info=True)
