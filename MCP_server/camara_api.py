import logging
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "DEBUG")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("camara-http-client")

BASE_URL = os.getenv("CAMARA_API_BASE_URL", "http://localhost:5020")


def camara_api_call(endpoint: str, method="GET", params=None, data=None):
    """
    Generic helper for calling CAMARA APIs.
    """
    url = f"{BASE_URL}{endpoint}"
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
