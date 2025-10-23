from datetime import datetime, timedelta
from typing import Dict, Any
import random

# Verification constants
class VerificationResult:
    TRUE = "TRUE"
    FALSE = "FALSE"
    PARTIAL = "PARTIAL"


def verify_device_location(body: Dict[str, Any]) -> tuple:
    """
    POST /verify
    Verify if a device is within a specified area
    """
    try:
        device = body.get("device", {})
        area = body.get("area", {})
        max_age = body.get("maxAge", 60)

        if not device or not area:
            return {"status": 400, "code": "INVALID_ARGUMENT", "message": "Device and area required"}, 400

        if area.get("areaType") != "CIRCLE":
            return {"status": 400, "code": "INVALID_ARGUMENT", "message": "Only CIRCLE areaType supported"}, 400

        radius = area.get("radius")
        if radius is None or radius <= 0:
            return {"status": 400, "code": "INVALID_ARGUMENT", "message": "Valid radius required"}, 400

        verification_result = _simulate_location_verification()
        last_location_time = datetime.utcnow() - timedelta(seconds=random.randint(0, max_age))

        response = {
            "verificationResult": verification_result,
            "lastLocationTime": last_location_time.isoformat() + "Z"
        }

        return response, 200

    except Exception as e:
        return {"status": 400, "code": "INVALID_ARGUMENT", "message": str(e)}, 400


def _simulate_location_verification() -> str:
    outcomes = [VerificationResult.TRUE] * 7 + [VerificationResult.FALSE] * 2 + [VerificationResult.PARTIAL]
    return random.choice(outcomes)
