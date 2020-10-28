import uuid
from typing import Optional

from pydantic import BaseModel, validator


class RegistrationBase(BaseModel):
    mobile: str

    @validator("mobile")
    def valid_mobile_number(cls, v: str):
        if len(v) == 13 and v[1:].isdigit() and v.startswith("+989"):
            return v
        raise ValueError("Mobile phone number must be like +989xxxxxxxxx")


class RegistrationCreate(RegistrationBase):
    pass


class RegistrationUpdate(RegistrationBase):
    pass


class RegistrationInDBBase(RegistrationBase):
    id: uuid.UUID
    mobile_is_verified: bool = False
    valid_for: int

    class Config:
        orm_mode = True


class Registration(RegistrationInDBBase):
    pass


class RegistrationInDB(RegistrationInDBBase):
    otp_id: Optional[uuid.UUID] = None
