from pydantic import BaseModel
from typing import Literal


class Center(BaseModel):
    latitude: float
    longitude: float


class Area(BaseModel):
    areaType: Literal["CIRCLE"]
    center: Center
    radius: int


class Device(BaseModel):
    phoneNumber: str


class VerifyRequest(BaseModel):
    device: Device
    area: Area
    maxAge: int


class VerifyResponse(BaseModel):
    verificationResult: Literal["TRUE", "FALSE"]
    lastLocationTime: str
