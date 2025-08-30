from flask import Flask, jsonify, request
import uuid
from datetime import datetime, timezone

app = Flask(__name__)

# Example service catalog following CAMARA API style
service_catalog = {
    "services": [
        {
            "serviceId": "device-location",
            "name": "Device Location",
            "description": "Provides geolocation data for a device.",
            "apis": [
                {
                    "apiName": "Get Location",
                    "endpoint": "/apis/device-location/v1/location",
                    "method": "GET",
                    "description": "Retrieve the current location of a device."
                }
            ]
        },
        {
            "serviceId": "quality-on-demand",
            "name": "Quality on Demand",
            "description": "Allows requesting network QoS information for specific sessions.",
            "apis": [
                {
                    "apiName": "Get QoD Session",
                    "endpoint": "/apis/quality-on-demand/v1/session",
                    "method": "GET",
                    "description": "Retrieve QoS information for a specific IMSI and PDU session."
                }
            ]
        },
        {
            "serviceId": "sms-messaging",
            "name": "SMS Messaging",
            "description": "Send and receive SMS messages.",
            "apis": [
                {
                    "apiName": "Send SMS",
                    "endpoint": "/apis/sms-messaging/v1/send",
                    "method": "GET",
                    "description": "Send an SMS message to a device."
                }
            ]
        },
        {
            "serviceId": "device-reachability",
            "name": "Device Reachability",
            "description": "Check if a device is online and reachable.",
            "apis": [
                {
                    "apiName": "Check Reachability",
                    "endpoint": "/apis/device-reachability/v1/check",
                    "method": "GET",
                    "description": "Check if a device is currently reachable."
                }
            ]
        },
        {
            "serviceId": "number-verification",
            "name": "Number Verification",
            "description": "Verify ownership of a mobile number.",
            "apis": [
                {
                    "apiName": "Verify Number",
                    "endpoint": "/apis/number-verification/v1/verify",
                    "method": "GET",
                    "description": "Verify a user’s phone number."
                }
            ]
        }
    ]
}

qod_sessions = {}
timestamp = datetime.now(timezone.utc).isoformat()

@app.route("/catalog", methods=["GET"])
def get_catalog():
    """Return the service catalog."""
    return jsonify(service_catalog), 200


@app.route("/apis/device-location/v1/location", methods=["GET"])
def get_device_location():
    """Simulated device location API."""
    device_id = request.args.get("deviceId", "unknown")
    location = {
        "deviceId": device_id,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "timestamp": timestamp
    }
    return jsonify(location), 200


@app.route("/apis/quality-on-demand/v1/session", methods=["GET"])
def get_qod_session():
    """Return a simulated QoD session for IMSI and PDU session."""
    imsi = request.args.get("imsi")
    pdu_session = request.args.get("pduSession")
    qos_profile = request.args.get("qosProfile", "standard")

    if not imsi or not pdu_session:
        return jsonify({"error": "Missing required parameters: imsi and pduSession"}), 400

    qos_session = {
        "imsi": imsi,
        "pduSession": pdu_session,
        "qosProfile": qos_profile,
        "bandwidth": "100Mbps" if qos_profile == "premium" else "20Mbps",
        "latency": "2ms" if qos_profile == "premium" else "5ms",
        "status": "active",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    return jsonify(qos_session), 200


@app.route("/apis/sms-messaging/v1/send", methods=["GET"])
def send_sms():
    """Simulated SMS send API."""
    to_number = request.args.get("to")
    content = request.args.get("content")
    sms_response = {
        "messageId": "msg123",
        "to": to_number,
        "content": content,
        "status": "delivered"
    }
    return jsonify(sms_response), 200


@app.route("/apis/device-reachability/v1/check", methods=["GET"])
def check_reachability():
    """Simulated device reachability API."""
    device_id = request.args.get("deviceId")
    reachability = {
        "deviceId": device_id,
        "reachable": True,
        "checkedAt": timestamp
    }
    return jsonify(reachability), 200


@app.route("/apis/number-verification/v1/verify", methods=["GET"])
def verify_number():
    """Simulated number verification API."""
    phone_number = request.args.get("phoneNumber")
    verification = {
        "phoneNumber": phone_number,
        "verified": True,
        "method": "sms-otp",
        "verifiedAt": timestamp
    }
    return jsonify(verification), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
