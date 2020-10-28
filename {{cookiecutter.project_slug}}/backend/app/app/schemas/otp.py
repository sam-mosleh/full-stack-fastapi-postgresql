import uuid
from typing import Optional

from pydantic import BaseModel, validator


class OTPBase(BaseModel):
    mobile: str

    @validator("mobile")
    def valid_mobile_number(cls, v: str):
        if len(v) == 13 and v[1:].isdigit() and v.startswith("+989"):
            return v
        raise ValueError("Mobile phone number must be like +989xxxxxxxxx")


class OTPCreate(OTPBase):
    verification_id: int
    verification_code: int


# class OTPUpdate(OTPBase):
#     pass


class OTPInDBBase(OTPBase):
    id: uuid.UUID
    valid_for: int

    class Config:
        orm_mode = True


class OTP(OTPInDBBase):
    pass


class OTPInDB(OTPInDBBase):
    verification_id: int
    verification_code: int
