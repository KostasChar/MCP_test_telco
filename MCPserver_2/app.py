import logging
from mcp.server.fastmcp import FastMCP
from MCPserver_2.tools.qod import create_qod_session, get_qod_session, delete_qod_session

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MCP server")

app = FastMCP("MCP Server")

# Register tools
app.tool()(create_qod_session)
app.tool()(get_qod_session)
app.tool()(delete_qod_session)

if __name__ == "__main__":
    logger.info("Starting QoS MCP Server (proxy mode)...")
    try:
        app.run(transport="streamable-http")
    except Exception as e:
        logger.critical("MCP server crashed: %s", e, exc_info=True)
