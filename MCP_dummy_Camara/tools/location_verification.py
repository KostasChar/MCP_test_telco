import os
import json
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv
from MCP_dummy_Camara.models.location_verfication_models import VerifyRequest, VerifyResponse
import json

logger = logging.getLogger(__name__)

# Calculate the path to the root .env file
root_dir = Path(__file__).resolve().parent.parent  # go up one level from tools/
env_path = root_dir / ".env"

# Load the .env file
load_dotenv(dotenv_path=env_path)
SESSION_SERVICE_URL = os.getenv("DUMMY_BACKEND_URL")


def verify_device_location(inp: VerifyRequest) -> VerifyResponse:
    """
    Verify device location by sending a request to the external verification endpoint using requests.
    """
    payload = {
        "device": {
            "phoneNumber": inp.device.phoneNumber
        },
        "area": {
            "areaType": inp.area.areaType,
            "center": {
                "latitude": inp.area.center.latitude,
                "longitude": inp.area.center.longitude
            },
            "radius": inp.area.radius
        },
        "maxAge": inp.maxAge
    }

    url = f"{SESSION_SERVICE_URL}/verify"

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        resp_json = response.json()
    except requests.RequestException as e:
        logger.error("Failed to send request to verification service: %s", e)
        raise

    logger.debug("Raw response: %s", json.dumps(resp_json, indent=2))

    return VerifyResponse(
        verificationResult=resp_json.get("verificationResult", "FALSE"),
        lastLocationTime=resp_json.get("lastLocationTime", "")
    )

