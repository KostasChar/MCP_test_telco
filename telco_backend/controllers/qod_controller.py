import uuid
from datetime import datetime, timezone
from app import qod_sessions

def current_time():
    return datetime.now(timezone.utc).isoformat()

def create_qod_session(body=None):
    body = body or {}
    phone_number = body.get("phoneNumber", "123456789")
    qos_profile = body.get("qosProfile", "QCI_1_voice")

    qos_session = {
        "sessionId": str(uuid.uuid4()),
        "duration": 86400,
        "device": {
            "phoneNumber": phone_number,
            "networkAccessIdentifier": f"{phone_number}@domain.com",
            "ipv4Address": {"publicAddress": "84.125.93.10", "publicPort": 59765},
            "ipv6Address": "2001:db8:85a3:8d3:1319:8a2e:370:7344"
        },
        "applicationServer": {
            "ipv4Address": "192.168.0.1/24",
            "ipv6Address": "2001:db8:85a3:8d3:1319:8a2e:370:7344"
        },
        "devicePorts": {"ranges": [{"from": 5010, "to": 5020}], "ports": [5060, 5070]},
        "applicationServerPorts": {"ranges": [{"from": 5010, "to": 5020}], "ports": [5060, 5070]},
        "qosProfile": qos_profile,
        "webhook": {"notificationUrl": "https://application-server.com", "notificationAuthToken": "c8974e592c2fa383d4a3960714"},
        "status": "active",
        "createdAt": current_time()
    }

    qod_sessions[qos_session["sessionId"]] = qos_session
    return qos_session, 200

def get_qod_session(sessionId):
    session = qod_sessions.get(sessionId)
    if not session:
        return {"error": "QoD session not found"}, 404
    return session, 200

def delete_qod_session(sessionId):
    session = qod_sessions.pop(sessionId, None)
    if not session:
        return {"error": "QoD session not found"}, 404
    session["status"] = "released"
    session["releasedAt"] = current_time()
    return session, 200
