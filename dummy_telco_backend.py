from flask import Flask, jsonify, request
import uuid
from datetime import datetime, timezone

app = Flask(__name__)

# --- In-memory data stores ---
qod_sessions = {}

# --- Service catalog (CAMARA-style) ---
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
            "description": "QoD session lifecycle management APIs.",
            "apis": [
                {
                    "apiName": "Create QoD Session",
                    "endpoint": "/apis/quality-on-demand/v1/sessions",
                    "method": "POST",
                    "description": "Create a new QoD session."
                },
                {
                    "apiName": "Get QoD Session",
                    "endpoint": "/apis/quality-on-demand/v1/sessions/{sessionId}",
                    "method": "GET",
                    "description": "Retrieve an existing QoD session."
                },
                {
                    "apiName": "Delete QoD Session",
                    "endpoint": "/apis/quality-on-demand/v1/sessions/{sessionId}",
                    "method": "DELETE",
                    "description": "Release an existing QoD session."
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
                    "method": "POST",
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


# --- Helpers ---
def current_time():
    return datetime.now(timezone.utc).isoformat()


# --- Service Catalog API ---
@app.route("/catalog", methods=["GET"])
def get_catalog():
    return jsonify(service_catalog), 200


# --- Device Location API ---
@app.route("/apis/device-location/v1/location", methods=["GET"])
def get_device_location():
    device_id = request.args.get("deviceId", "unknown")
    location = {
        "deviceId": device_id,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "timestamp": current_time()
    }
    return jsonify(location), 200


# --- Quality on Demand (QoD) APIs ---
@app.route("/apis/quality-on-demand/v1/sessions", methods=["POST"])
def create_qod_session():
    data = request.get_json() or {}
    phone_number = data.get("phoneNumber", "123456789")
    qos_profile = data.get("qosProfile", "QCI_1_voice")

    qos_session = {
        "sessionId": str(uuid.uuid4()),
        "duration": 86400,
        "device": {
            "phoneNumber": phone_number,
            "networkAccessIdentifier": f"{phone_number}@domain.com",
            "ipv4Address": {
                "publicAddress": "84.125.93.10",
                "publicPort": 59765
            },
            "ipv6Address": "2001:db8:85a3:8d3:1319:8a2e:370:7344"
        },
        "applicationServer": {
            "ipv4Address": "192.168.0.1/24",
            "ipv6Address": "2001:db8:85a3:8d3:1319:8a2e:370:7344"
        },
        "devicePorts": {
            "ranges": [{"from": 5010, "to": 5020}],
            "ports": [5060, 5070]
        },
        "applicationServerPorts": {
            "ranges": [{"from": 5010, "to": 5020}],
            "ports": [5060, 5070]
        },
        "qosProfile": qos_profile,
        "webhook": {
            "notificationUrl": "https://application-server.com",
            "notificationAuthToken": "c8974e592c2fa383d4a3960714"
        },
        "status": "active",
        "createdAt": current_time()
    }

    # Optional: store in memory if you want GET/DELETE later
    qod_sessions[qos_session["sessionId"]] = qos_session
    return jsonify(qos_session), 200



@app.route("/apis/quality-on-demand/v1/sessions/<session_id>", methods=["GET"])
def get_qod_session(session_id):
    session = qod_sessions.get(session_id)
    if not session:
        return jsonify({"error": "QoD session not found"}), 404
    return jsonify(session), 200


@app.route("/apis/quality-on-demand/v1/sessions/<session_id>", methods=["DELETE"])
def delete_qod_session(session_id):
    session = qod_sessions.pop(session_id, None)
    if not session:
        return jsonify({"error": "QoD session not found"}), 404
    session["status"] = "released"
    session["releasedAt"] = current_time()
    return jsonify(session), 200


# --- SMS Messaging API ---
@app.route("/apis/sms-messaging/v1/send", methods=["POST"])
def send_sms():
    data = request.get_json() or {}
    to_number = data.get("to")
    content = data.get("content")
    sms_response = {
        "messageId": str(uuid.uuid4()),
        "to": to_number,
        "content": content,
        "status": "delivered"
    }
    return jsonify(sms_response), 200


# --- Device Reachability API ---
@app.route("/apis/device-reachability/v1/check", methods=["GET"])
def check_reachability():
    device_id = request.args.get("deviceId", "unknown")
    reachability = {
        "deviceId": device_id,
        "reachable": True,
        "checkedAt": current_time()
    }
    return jsonify(reachability), 200


# --- Number Verification API ---
@app.route("/apis/number-verification/v1/verify", methods=["GET"])
def verify_number():
    phone_number = request.args.get("phoneNumber", "unknown")
    verification = {
        "phoneNumber": phone_number,
        "verified": True,
        "method": "sms-otp",
        "verifiedAt": current_time()
    }
    return jsonify(verification), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
