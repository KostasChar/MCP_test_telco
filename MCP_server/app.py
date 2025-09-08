import logging
import requests
from mcp.server.fastmcp import FastMCP

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("camara-mcp-server")

mcp = FastMCP("camara-mcp-server")


# Shared helper
def _fetch_from_api(endpoint: str, method="GET", params=None, data=None):
    url = f"http://localhost:5000{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, params=params, timeout=5)
        elif method == "POST":
            resp = requests.post(url, json=data, timeout=5)
        elif method == "DELETE":
            resp = requests.delete(url, timeout=5)
        else:
            raise ValueError(f"Unsupported method {method}")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("Error calling %s: %s", url, e, exc_info=True)
        return {"status": "error", "message": str(e)}


# Service catalog resource
@mcp.resource("resource://service_catalog")
def service_catalog():
    """Available CAMARA services and their metadata."""
    return _fetch_from_api("/catalog")


# Tools

@mcp.tool()
def get_catalog():
    """Retrieve the service catalog (live)."""
    return _fetch_from_api("/catalog")


@mcp.tool()
def get_device_location(deviceId: str):
    """Retrieve device location."""
    return _fetch_from_api("/apis/device-location/v1/location", params={"deviceId": deviceId})


# QoD
@mcp.tool()
def create_qod_session(phoneNumber: str, qosProfile: str = "QCI_1_voice"):
    """Create a new QoD session with a phone number and QoS profile."""
    payload = {
        "phoneNumber": phoneNumber,
        "qosProfile": qosProfile
    }
    return _fetch_from_api("/apis/quality-on-demand/v1/sessions", method="POST", data=payload)


@mcp.tool()
def get_qod_session(sessionId: str):
    """Retrieve an existing QoD session by sessionId."""
    return _fetch_from_api(f"/apis/quality-on-demand/v1/sessions/{sessionId}")


@mcp.tool()
def delete_qod_session(sessionId: str):
    """Release an existing QoD session by sessionId."""
    return _fetch_from_api(f"/apis/quality-on-demand/v1/sessions/{sessionId}", method="DELETE")


@mcp.tool()
def send_sms(to: str, content: str):
    """Send an SMS message."""
    return _fetch_from_api("/apis/sms-messaging/v1/send", method="POST", data={"to": to, "content": content})


@mcp.tool()
def check_reachability(deviceId: str):
    """Check if a device is reachable."""
    return _fetch_from_api("/apis/device-reachability/v1/check", params={"deviceId": deviceId})


@mcp.tool()
def verify_number(phoneNumber: str):
    """Verify a phone number."""
    return _fetch_from_api("/apis/number-verification/v1/verify", params={"phoneNumber": phoneNumber})


if __name__ == "__main__":
    logger.info("Starting MCP server on camara-mcp-server")
    try:
    #mcp.run(transport="stdio")

      mcp.run(transport="streamable-http")
    except Exception as e:
        logger.critical("MCP server crashed: %s", e, exc_info=True)

