import uuid

def send_sms(body):
    to_number = body.get("to")
    content = body.get("content")
    return {
        "messageId": str(uuid.uuid4()),
        "to": to_number,
        "content": content,
        "status": "delivered"
    }, 200
