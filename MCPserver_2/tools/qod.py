import json
import logging
import requests
from pathlib import Path
from MCPserver_2.models.qod_models import *
import os
from dotenv import load_dotenv

##
# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MCP server")

# Calculate the path to the root .env file
root_dir = Path(__file__).resolve().parent.parent  # go up one level from tools/
env_path = root_dir / ".env"

# Load the .env file
load_dotenv(dotenv_path=env_path)

SESSION_SERVICE_URL = os.getenv("SESSION_SERVICE_URL")
if not SESSION_SERVICE_URL:
    raise EnvironmentError("SESSION_SERVICE_URL environment variable is not set")

async def create_qod_session(inp: CreateQoDSessionInput) -> QoDSessionMinimalResponse:
    """
    Create QoS session
    """

    # Load JSON template
    json_path = Path("json_templates/qod_request.json")
    if not json_path.exists():
        logger.error("Template file qod_request.json not found")
        raise FileNotFoundError("qod_request.json not found")

    with open(json_path, "r") as f:
        template = json.load(f)

    # Merge inputs into the template
    device_data = inp.device.model_dump(exclude_unset=True)
    template["device"].update(device_data)
    template["qosProfile"] = inp.qosProfile
    template["duration"] = inp.duration

    logger.debug("Final request payload: %s", json.dumps(template, indent=2))

    try:
        response = requests.post(f"{SESSION_SERVICE_URL}/sessions", json=template)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Failed to send request to session service: %s", e)
        raise

    resp_json = response.json()
    logger.debug("Raw response: %s", json.dumps(resp_json, indent=2))

    # Extract only needed fields
    return QoDSessionMinimalResponse(
        sessionId=resp_json.get("sessionId"),
        qosStatus=resp_json.get("qosStatus")
    )


async def get_qod_session(inp: GetQoDSessionInput) -> QoDSessionFullResponse:
    """
    Retrieves QoS session based on session id
    """

    session_url = f"{SESSION_SERVICE_URL}/sessions/{inp.sessionId}"
    logger.debug("Fetching session details from: %s", session_url)

    try:
        response = requests.get(session_url)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Failed to get session %s: %s", inp.sessionId, e)
        raise

    resp_json = response.json()
    logger.debug("Session details response: %s", json.dumps(resp_json, indent=2))

    # Return all session details
    return QoDSessionFullResponse(
        sessionId=resp_json.get("sessionId"),
        device=resp_json.get("device", {}),
        applicationServer=resp_json.get("applicationServer", {}),
        devicePorts=resp_json.get("devicePorts"),
        applicationServerPorts=resp_json.get("applicationServerPorts"),
        qosProfile=resp_json.get("qosProfile"),
        sink=resp_json.get("sink"),
        sinkCredential=resp_json.get("sinkCredential"),
        duration=resp_json.get("duration"),
        qosStatus=resp_json.get("qosStatus"),
        startedAt=resp_json.get("startedAt"),
        expiresAt=resp_json.get("expiresAt")
    )

async def delete_qod_session(inp: GetQoDSessionInput) -> str:
    """
    Delete QoS session by sessionId.
    """
    session_url = f"{SESSION_SERVICE_URL}/sessions/{inp.sessionId}"
    logger.debug("Deleting session at: %s", session_url)

    try:
        response = requests.delete(session_url)
        if response.status_code == 204:
            logger.info("Session %s deleted successfully", inp.sessionId)
            return "success"
        else:
            logger.warning(
                "Unexpected response deleting session %s: %s %s",
                inp.sessionId,
                response.status_code,
                response.text
            )
            response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Failed to delete session %s: %s", inp.sessionId, e)

