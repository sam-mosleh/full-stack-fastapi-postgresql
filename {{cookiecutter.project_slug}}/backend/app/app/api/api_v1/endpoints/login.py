import random
from datetime import timedelta
from typing import Any

import aioredis
import aioredlock
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.utils import (
    generate_password_reset_token,
    send_login_code,
    send_reset_password_email,
    verify_password_reset_token,
)

router = APIRouter()


@router.post("/login/otp/token", response_model=schemas.OTPToken)
def create_otp_token(
    username: str = Body(...),
    password: str = Body(...),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Create an OTP token for the user
    """
    user = crud.user.authenticate(db, username=username, password=password)
    if user is None:
        raise HTTPException(status_code=403, detail="Incorrect username or password")
    # elif not user.is_active:
    #     raise HTTPException(status_code=401, detail="Inactive user")
    otp_token_expires = timedelta(minutes=settings.OTP_TOKEN_EXPIRE_MINUTES)
    return {
        "otp_token": security.create_access_token(
            user.id, expires_delta=otp_token_expires
        ),
        "expires_in": otp_token_expires,
    }


@router.post(
    "/login/otp/send",
    response_model=schemas.OTPHashed,
    status_code=status.HTTP_201_CREATED,
)
async def send_otp(
    redis: aioredis.Redis = Depends(deps.get_redis),
    lock_manager: aioredlock.Aioredlock = Depends(deps.get_lock),
    current_user: schemas.UserInDB = Depends(deps.get_current_unverified_user),
) -> Any:
    """
    Send an OTP to the unverified user
    """
    try:
        lock = await lock_manager.lock(
            f"lock:otp:{current_user.id}", lock_timeout=settings.OTP_EXPIRE_SECONDS
        )
    except aioredlock.LockError:
        raise HTTPException(status_code=400, detail="User already has an active OTP")

    code = random.randint(1000, 9999)
    verification_id = await send_login_code(current_user.mobile, code=code)
    obj_in = schemas.OTPCreate(
        mobile=current_user.mobile,
        verification_id=verification_id,
        verification_code=code,
    )
    return await crud.otp_cache.create(redis, obj_in=obj_in, id=current_user.id)


@router.post("/login/access-token", response_model=schemas.Token)
async def create_access_token(
    code: int = Body(...),
    redis: aioredis.Redis = Depends(deps.get_redis),
    current_user: schemas.UserInDB = Depends(deps.get_current_unverified_user),
) -> Any:
    """
    Verify user by verification code sent to its mobile
    """
    otp = await crud.otp_cache.get(redis, id=current_user.id)
    if otp is None:
        raise HTTPException(
            status_code=404, detail="No active OTP found for the user",
        )
    if code != otp.verification_code:
        raise HTTPException(
            status_code=400, detail="Wrong verification code",
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            current_user.id, is_verified=True, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "expires_in": access_token_expires,
    }


@router.post("/login/test-token", response_model=schemas.User)
def test_token(current_user: schemas.UserInDB = Depends(deps.get_current_user)) -> Any:
    """
    Test access token
    """
    return current_user


@router.get("/login/refresh-token", response_model=schemas.Token)
def test_token(current_user: schemas.UserInDB = Depends(deps.get_current_user)) -> Any:
    """
    Refresh access token
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            current_user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/password-recovery/{email}", response_model=schemas.Msg)
def recover_password(email: str, db: Session = Depends(deps.get_db)) -> Any:
    """
    Password Recovery
    """
    user = crud.user.get_by_email(db, email=email)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    send_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    return {"msg": "Password recovery email sent"}


@router.post("/reset-password", response_model=schemas.Msg)
async def reset_password(
    token: str = Body(...),
    new_password: str = Body(...),
    db: Session = Depends(deps.get_db),
    redis: aioredis.Redis = Depends(deps.get_redis),
) -> Any:
    """
    Reset password
    """
    email = verify_password_reset_token(token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = await crud.user_cachedb.get_by_email(db, redis, email=email)
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    elif not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    user = await crud.user_cachedb.update(
        db, redis, cache_obj=user, obj_in={"password": new_password}
    )
    return {"msg": "Password updated successfully"}
