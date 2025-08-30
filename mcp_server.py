# server.py
import logging
import requests
from mcp.server.fastmcp import FastMCP

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG gives the most detail
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("camara-mcp-server")

mcp = FastMCP("camara-mcp-server")

# Tool: Get catalog
@mcp.tool()
def get_catalog():
    """Retrieve the service catalog from the Flask API."""
    logger.debug("Invoking get_catalog()")
    try:
        resp = requests.get("http://localhost:5000/catalog")
        resp.raise_for_status()
        logger.debug("Response: %s", resp.json())
        return resp.json()
    except Exception as e:
        logger.error("Error in get_catalog: %s", e, exc_info=True)
        return {"error": str(e)}

# Tool: Get device location
@mcp.tool()
def get_device_location(deviceId: str):
    """Retrieve device location."""
    logger.debug("Invoking get_device_location with deviceId=%s", deviceId)
    try:
        resp = requests.get("http://localhost:5000/apis/device-location/v1/location", params={"deviceId": deviceId})
        resp.raise_for_status()
        logger.debug("Response: %s", resp.json())
        return resp.json()
    except Exception as e:
        logger.error("Error in get_device_location: %s", e, exc_info=True)
        return {"error": str(e)}

# Tool: QoD session
@mcp.tool()
def get_qod_session(imsi: str, pduSession: str):
    """Request a QoD session for a given IMSI and PDU session."""
    logger.debug("Invoking get_qod_session with imsi=%s pduSession=%s qosProfile=%s", imsi, pduSession)
    try:
        resp = requests.get(
            "http://localhost:5000/apis/quality-on-demand/v1/session",
            params={"imsi": imsi, "pduSession": pduSession},
            timeout=5
        )
        resp.raise_for_status()
        logger.debug("Response: %s", resp.json())
        return resp.json()
    except Exception as e:
        logger.error("Error in get_qod_session: %s", e, exc_info=True)
        return {"error": str(e)}

# Tool: Send SMS
@mcp.tool()
def send_sms(to: str, content: str):
    """Send an SMS."""
    logger.debug("Invoking send_sms to=%s content=%s", to, content)
    try:
        resp = requests.get("http://localhost:5000/apis/sms-messaging/v1/send", params={"to": to, "content": content})
        resp.raise_for_status()
        logger.debug("Response: %s", resp.json())
        return resp.json()
    except Exception as e:
        logger.error("Error in send_sms: %s", e, exc_info=True)
        return {"error": str(e)}

# Tool: Check reachability
@mcp.tool()
def check_reachability(deviceId: str):
    """Check if device is reachable."""
    logger.debug("Invoking check_reachability with deviceId=%s", deviceId)
    try:
        resp = requests.get("http://localhost:5000/apis/device-reachability/v1/check", params={"deviceId": deviceId})
        resp.raise_for_status()
        logger.debug("Response: %s", resp.json())
        return resp.json()
    except Exception as e:
        logger.error("Error in check_reachability: %s", e, exc_info=True)
        return {"error": str(e)}

# Tool: Verify number
@mcp.tool()
def verify_number(phoneNumber: str):
    """Verify a phone number."""
    logger.debug("Invoking verify_number with phoneNumber=%s", phoneNumber)
    try:
        resp = requests.get("http://localhost:5000/apis/number-verification/v1/verify", params={"phoneNumber": phoneNumber})
        resp.raise_for_status()
        logger.debug("Response: %s", resp.json())
        return resp.json()
    except Exception as e:
        logger.error("Error in verify_number: %s", e, exc_info=True)
        return {"error": str(e)}

if __name__ == "__main__":
    logger.info("Starting MCP server on camara-mcp-server")
    try:
        mcp.run()
    except Exception as e:
        logger.critical("MCP server crashed: %s", e, exc_info=True)
