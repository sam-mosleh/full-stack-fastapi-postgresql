import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, validator


# Regular members related shared properties
class UnprivilegedUserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None


# Properties to receive via API on creation by regular members
class UnprivilegedUserCreate(UnprivilegedUserBase):
    password: str


# Properties to receive via API on update by regular members
class UnprivilegedUserUpdate(UnprivilegedUserBase):
    username: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str] = None

    @validator("password")
    def prevent_none(cls, v):
        assert v is not None, "password may not be empty"
        return v


# Shared properties
class UserBase(UnprivilegedUserBase):
    mobile: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False

    @validator("mobile")
    def valid_mobile_number(cls, v: Optional[str]):
        if v is None:
            return None
        if len(v) == 13 and v[1:].isdigit() and v.startswith("+989"):
            return v
        raise ValueError("Mobile phone number must be like +989xxxxxxxxx")


# Properties to receive via API on creation
class UserCreate(UserBase):
    mobile: str
    password: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

    @validator("username")
    def prevent_none_username(cls, v):
        assert v is not None, "username may not be empty"
        return v

    @validator("email")
    def prevent_none_email(cls, v):
        assert v is not None, "email may not be empty"
        return v

    @validator("password")
    def prevent_none_password(cls, v):
        assert v is not None, "password may not be empty"
        return v


class UserInDBBase(UserBase):
    id: uuid.UUID
    mobile: str

    class Config:
        orm_mode = True


# Additional properties to return via API
class User(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
