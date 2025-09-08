from flask import jsonify

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
                {"apiName": "Create QoD Session", "endpoint": "/apis/quality-on-demand/v1/sessions", "method": "POST"},
                {"apiName": "Get QoD Session", "endpoint": "/apis/quality-on-demand/v1/sessions/{sessionId}", "method": "GET"},
                {"apiName": "Delete QoD Session", "endpoint": "/apis/quality-on-demand/v1/sessions/{sessionId}", "method": "DELETE"}
            ]
        },
        {
            "serviceId": "sms-messaging",
            "name": "SMS Messaging",
            "description": "Send and receive SMS messages.",
            "apis": [{"apiName": "Send SMS", "endpoint": "/apis/sms-messaging/v1/send", "method": "POST"}]
        },
        {
            "serviceId": "device-reachability",
            "name": "Device Reachability",
            "description": "Check if a device is online and reachable.",
            "apis": [{"apiName": "Check Reachability", "endpoint": "/apis/device-reachability/v1/check", "method": "GET"}]
        },
        {
            "serviceId": "number-verification",
            "name": "Number Verification",
            "description": "Verify ownership of a mobile number.",
            "apis": [{"apiName": "Verify Number", "endpoint": "/apis/number-verification/v1/verify", "method": "GET"}]
        }
    ]
}


def get_catalog():
    return service_catalog, 200
