from datetime import datetime
from flask import jsonify

def retrieve_device_location(body):
    """
    Handle POST /retrieve
    """
    try:
        device = body.get("device", {})
        phone_number = device.get("phoneNumber")
        max_age = body.get("maxAge")

        if not phone_number or not isinstance(max_age, int):
            return jsonify({"error": "Invalid request body"}), 400

        # Dummy location response (replace with DB lookup or transformation function)
        response = {
            "lastLocationTime": datetime.utcnow().isoformat() + "Z",
            "area": {
                "areaType": "CIRCLE",
                "center": {
                    "latitude": 45.754114,
                    "longitude": 4.860374
                },
                "radius": 800
            }
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
