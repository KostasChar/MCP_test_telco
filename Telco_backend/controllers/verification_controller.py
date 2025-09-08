from datetime import datetime, timezone

def current_time():
    return datetime.now(timezone.utc).isoformat()

def verify_number(phoneNumber=None):
    return {
        "phoneNumber": phoneNumber or "unknown",
        "verified": True,
        "method": "sms-otp",
        "verifiedAt": current_time()
    }, 200
