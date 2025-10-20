import logging
import requests
from dotenv import load_dotenv
from pathlib import Path
import os
# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MCP server")

# Calculate the path to the root .env file
root_dir = Path(__file__).resolve().parent.parent  # go up one level from tools/
env_path = root_dir / ".env"

# Load the .env file
load_dotenv(dotenv_path=env_path)
SESSION_SERVICE_URL = os.getenv("ISI_URL")

async def get_app_definitions() -> dict:
    """
    Get the list of all existing Application definitions from the Edge Cloud Provider
    that the user has permission to view.
    """
    url = f"{SESSION_SERVICE_URL}/apps"
    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers, allow_redirects=True)
    response.raise_for_status()
    data = response.json()

    # Ensure the result is a dict for FastMCP compatibility
    if isinstance(data, list):
        return {"applications": data}
    return data