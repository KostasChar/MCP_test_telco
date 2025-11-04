from datetime import datetime, timedelta
from typing import Dict, Any
import uuid

# In-memory session storage
sessions_db: Dict[str, Dict[str, Any]] = {}

class QoSStatus:
    REQUESTED = "REQUESTED"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"

def create_session(body: Dict[str, Any]) -> tuple:
    """
    POST /sessions
    Create a new QoS session
    """
    try:
        session_id = str(uuid.uuid4())
        device = body.get("device", {})
        app_server = body.get("applicationServer", {})
        qos_profile = body.get("qosProfile", "QOS_L")
        sink = body.get("sink")
        duration = body.get("duration", 3600)

        # Validate required fields
        if not app_server or not sink:
            return {
                "status": 422,
                "code": "MISSING_FIELD",
                "message": "applicationServer and sink are required"
            }, 422

        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=duration)

        session = {
            "sessionId": session_id,
            "device": device,
            "applicationServer": app_server,
            "devicePorts": body.get("devicePorts", {"ranges": [], "ports": []}),
            "applicationServerPorts": body.get("applicationServerPorts", {"ranges": [], "ports": []}),
            "qosProfile": qos_profile,
            "sink": sink,
            "sinkCredential": body.get("sinkCredential", {}),
            "duration": duration,
            "qosStatus": QoSStatus.REQUESTED,
            "createdAt": now.isoformat() + "Z",
            "startedAt": now.isoformat() + "Z",
            "expiresAt": expires_at.isoformat() + "Z",
        }

        sessions_db[session_id] = session

        # Response excludes device
        response = {
            "sessionId": session_id,
            "applicationServer": app_server,
            "qosProfile": qos_profile,
            "sink": sink,
            "duration": duration,
            "qosStatus": QoSStatus.REQUESTED
        }

        return response, 201

    except Exception as e:
        return {
            "status": 400,
            "code": "INVALID_ARGUMENT",
            "message": f"Client specified an invalid argument: {str(e)}"
        }, 400

def get_session(sessionId: str) -> tuple:
    """
    GET /sessions/{sessionId}
    Retrieve QoS session information
    """
    session = sessions_db.get(sessionId)
    if not session:
        return {
            "status": 404,
            "code": "NOT_FOUND",
            "message": "Session not found"
        }, 404

    response = {
        "sessionId": session["sessionId"],
        "duration": session["duration"],
        "applicationServer": session["applicationServer"],
        "qosProfile": session["qosProfile"],
        "sink": session["sink"],
        "startedAt": session["startedAt"],
        "expiresAt": session["expiresAt"],
        "qosStatus": session["qosStatus"]
    }
    return response, 200

def delete_session(sessionId: str) -> tuple:
    """
    DELETE /sessions/{sessionId}
    Delete a QoS session
    """
    session = sessions_db.get(sessionId)
    if not session:
        return {
            "status": 404,
            "code": "NOT_FOUND",
            "message": "Session not found"
        }, 404

    # Mark as UNAVAILABLE before deletion if it was AVAILABLE
    if session["qosStatus"] == QoSStatus.AVAILABLE:
        session["qosStatus"] = QoSStatus.UNAVAILABLE
        # Normally, send a notification callback here

    del sessions_db[sessionId]
    return "", 204

def retrieve_sessions(body: Dict[str, Any]) -> tuple:
    """
    POST /retrieve-sessions
    Retrieve QoS sessions associated with a specific device
    """
    try:
        device = body.get("device", {})
        if not device:
            return {
                "status": 422,
                "code": "MISSING_FIELD",
                "message": "Device field is required"
            }, 422

        phone_number = device.get("phoneNumber")
        network_id = device.get("networkAccessIdentifier")
        ipv4_address = device.get("ipv4Address", {}).get("publicAddress")
        ipv6_address = device.get("ipv6Address")

        # Search for sessions that match any device identifier
        matched_sessions = []
        for session in sessions_db.values():
            session_device = session.get("device", {})
            if (
                session_device.get("phoneNumber") == phone_number
                or session_device.get("networkAccessIdentifier") == network_id
                or session_device.get("ipv4Address", {}).get("publicAddress") == ipv4_address
                or session_device.get("ipv6Address") == ipv6_address
            ):
                matched_sessions.append({
                    "applicationServer": session["applicationServer"],
                    "qosProfile": session["qosProfile"],
                    "sink": session["sink"],
                    "sessionId": session["sessionId"],
                    "duration": session["duration"],
                    "startedAt": session["startedAt"],
                    "expiresAt": session["expiresAt"],
                    "qosStatus": session["qosStatus"]
                })

        if not matched_sessions:
            return {
                "status": 404,
                "code": "NOT_FOUND",
                "message": "No sessions found for the specified device"
            }, 404

        return matched_sessions, 200

    except Exception as e:
        return {
            "status": 400,
            "code": "INVALID_ARGUMENT",
            "message": f"Client specified an invalid argument: {str(e)}"
        }, 400
