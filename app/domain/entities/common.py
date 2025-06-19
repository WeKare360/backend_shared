from typing import Optional
from enum import Enum
from pydantic import BaseModel

class Address(BaseModel):
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    state_code: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "US"

class ContactInfo(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None

class GenderEnum(str, Enum):
    male = "M"
    female = "F"
    unknown = "U"

class StatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"
    pending = "pending"
    cancelled = "cancelled"