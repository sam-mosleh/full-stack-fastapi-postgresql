import uuid
from datetime import timedelta

from pydantic import BaseModel


class OTPToken(BaseModel):
    otp_token: str
    expires_in: timedelta


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: timedelta


class TokenPayload(BaseModel):
    sub: uuid.UUID
    is_verified: bool
