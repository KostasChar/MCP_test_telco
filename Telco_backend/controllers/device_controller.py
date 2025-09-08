from datetime import datetime, timezone

def current_time():
    return datetime.now(timezone.utc).isoformat()

def get_device_location(deviceId=None):
    location = {
        "deviceId": deviceId or "unknown",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "timestamp": current_time()
    }
    return location, 200

def check_reachability(deviceId=None):
    return {
        "deviceId": deviceId or "unknown",
        "reachable": True,
        "checkedAt": current_time()
    }, 200
