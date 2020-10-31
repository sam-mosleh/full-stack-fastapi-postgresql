import uuid
from typing import Optional

from pydantic import BaseModel, validator


class OTPBase(BaseModel):
    mobile: str


class OTPCreate(OTPBase):
    verification_id: Optional[int]
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


class OTPHashed(OTPInDBBase):
    @validator("mobile")
    def hash_mobile(cls, v: str):
        return f"{v[:6]}xxxxx{v[-2:]}"


class OTPInDB(OTPInDBBase):
    verification_id: Optional[int]
    verification_code: int


class OTPVerification(BaseModel):
    code: int
