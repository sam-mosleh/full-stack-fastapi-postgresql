import uuid

from pydantic import BaseModel


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


class OTPVerification(BaseModel):
    code: int
