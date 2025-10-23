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
