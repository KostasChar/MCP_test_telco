import logging
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from camara_api import camara_api_call

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "DEBUG")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("camara-mcp-server")

MCP_SERVER_NAME = os.getenv("MCP_SERVER_NAME", "camara-mcp-server")
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "streamable-http")

mcp = FastMCP(MCP_SERVER_NAME)

# Service catalog resource
# @mcp.resource("resource://service_catalog")
# def service_catalog():
#     """Available CAMARA services and their metadata."""
#     return camara_api_call("/catalog")


# Tools
@mcp.tool()
def get_catalog():
    return camara_api_call("/catalog")


@mcp.tool()
def get_device_location(deviceId: str):
    return camara_api_call("/apis/device-location/v1/location", params={"deviceId": deviceId})


@mcp.tool()
def create_qod_session(phoneNumber: str, qosProfile: str = "QCI_1_voice"):
    payload = {"phoneNumber": phoneNumber, "qosProfile": qosProfile}
    return camara_api_call("/apis/quality-on-demand/v1/sessions", method="POST", data=payload)


@mcp.tool()
def get_qod_session(sessionId: str):
    return camara_api_call(f"/apis/quality-on-demand/v1/sessions/{sessionId}")


@mcp.tool()
def delete_qod_session(sessionId: str):
    return camara_api_call(f"/apis/quality-on-demand/v1/sessions/{sessionId}", method="DELETE")


@mcp.tool()
def send_sms(to: str, content: str):
    return camara_api_call("/apis/sms-messaging/v1/send", method="POST", data={"to": to, "content": content})


@mcp.tool()
def check_reachability(deviceId: str):
    return camara_api_call("/apis/device-reachability/v1/check", params={"deviceId": deviceId})


@mcp.tool()
def verify_number(phoneNumber: str):
    return camara_api_call("/apis/number-verification/v1/verify", params={"phoneNumber": phoneNumber})


if __name__ == "__main__":
    logger.info(f"Starting MCP server '{MCP_SERVER_NAME}' with transport '{MCP_TRANSPORT}'")
    try:
        mcp.run(transport=MCP_TRANSPORT)
    except Exception as e:
        logger.critical("MCP server crashed: %s", e, exc_info=True)
