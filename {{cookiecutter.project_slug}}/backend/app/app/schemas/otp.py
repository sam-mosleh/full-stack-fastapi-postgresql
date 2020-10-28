import uuid
from typing import Optional

from pydantic import BaseModel, validator


class OTPBase(BaseModel):
    mobile: str


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
