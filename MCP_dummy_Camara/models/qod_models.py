from ipaddress import IPv6Address

from pydantic import BaseModel, model_validator
from typing import Optional, Dict, Any
class IPv4Address(BaseModel):
    publicAddress: str
    publicPort: int

class DeviceInput(BaseModel):
    phoneNumber: Optional[str] = None
    networkAccessIdentifier: Optional[str] = None
    ipv4Address: Optional[IPv4Address] = None
    ipv6Address: Optional[IPv6Address] = None

    @model_validator(mode='before')
    @classmethod
    def check_one_identifier(cls, values):
        if isinstance(values, dict):
            if not (values.get("phoneNumber") or values.get("networkAccessIdentifier") or values.get("ipv4Address")) or values.get("ipv6Address"):
                raise ValueError(
                    "Device must include at least one of: phoneNumber, networkAccessIdentifier, or ipv4Address or ipv6Address"
                )
        return values

class CreateQoDSessionInput(BaseModel):
    device: DeviceInput
    qosProfile: str
    duration: int

# ----- Output schema -----
class QoDSessionMinimalResponse(BaseModel):
    sessionId: str
    qosStatus: str

class GetQoDSessionInput(BaseModel):
    sessionId: str

class QoDSessionFullResponse(BaseModel):
    sessionId: str
    device: Dict[str, Any]
    applicationServer: Dict[str, Any]
    devicePorts: Optional[Dict[str, Any]] = None
    applicationServerPorts: Optional[Dict[str, Any]] = None
    qosProfile: str
    sink: Optional[str] = None
    sinkCredential: Optional[Dict[str, Any]] = None
    duration: int
    qosStatus: str
    startedAt: Optional[str] = None
    expiresAt: Optional[str] = None


class QoDSessionsList(BaseModel):
    device: DeviceInput
