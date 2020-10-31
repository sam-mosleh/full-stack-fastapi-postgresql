import random
from typing import Any

import aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.core.config import settings
from app.utils import send_registration_code

router = APIRouter()


@router.post(
    "/", response_model=schemas.Registration, status_code=status.HTTP_201_CREATED
)
async def create_registration(
    registration_in: schemas.RegistrationCreate,
    db: Session = Depends(deps.get_db),
    redis: aioredis.Redis = Depends(deps.get_redis),
) -> Any:
    """
    Create new registration.
    """
    if not settings.USERS_OPEN_REGISTRATION:
        raise HTTPException(
            status_code=403,
            detail="Open user registration is forbidden on this server",
        )
    user = crud.user.get_by_mobile(db, mobile=registration_in.mobile)
    if user is not None:
        raise HTTPException(
            status_code=400, detail="User with specified mobile exists in the system",
        )
    return await crud.registration_cache.create(redis, obj_in=registration_in)


@router.get("/{id}", response_model=schemas.Registration)
def read_registration(
    registration: schemas.RegistrationInDB = Depends(deps.get_registration_by_id),
) -> Any:
    """
    Get a registration.
    """
    return registration


@router.post(
    "/{id}/mobile/send-otp",
    response_model=schemas.OTP,
    status_code=status.HTTP_201_CREATED,
)
async def send_registration_otp(
    registration: schemas.RegistrationInDB = Depends(deps.get_registration_by_id),
    redis: aioredis.Redis = Depends(deps.get_redis),
) -> Any:
    """
    Send an OTP to registration mobile phone number.
    """
    if registration.otp_id is not None:
        otp_exists = await crud.otp_cache.exists(redis, id=registration.otp_id)
        if otp_exists:
            raise HTTPException(
                status_code=409, detail="Registration has an active OTP.",
            )
    code = random.randint(1000, 9999)
    verification_id = await send_registration_code(registration.mobile, code=code)
    obj_in = schemas.OTPCreate(
        mobile=registration.mobile,
        verification_id=verification_id,
        verification_code=code,
    )
    otp = await crud.otp_cache.create(redis, obj_in=obj_in)
    await crud.registration_cache.set_otp(redis, cache_obj=registration, otp=otp)
    return otp


@router.post(
    "/{id}/mobile/verify", response_model=schemas.Registration,
)
async def verify_registration_mobile(
    *,
    registration: schemas.RegistrationInDB = Depends(
        deps.get_unverified_registration_by_id
    ),
    verification: schemas.OTPVerification,
    redis: aioredis.Redis = Depends(deps.get_redis),
) -> Any:
    """
    verify a registration mobile phone number.
    """
    otp = await crud.otp_cache.get(redis, id=registration.otp_id)
    if otp is None:
        raise HTTPException(
            status_code=404, detail="No active OTP found on the registration",
        )
    if verification.code != otp.verification_code:
        raise HTTPException(
            status_code=400, detail="Wrong verification",
        )
    return await crud.registration_cache.verify_mobile(redis, cache_obj=registration)


@router.post("/{id}", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    registration: schemas.RegistrationInDB = Depends(
        deps.get_verified_registration_by_id
    ),
    user_in: schemas.UnprivilegedUserCreate,
    db: Session = Depends(deps.get_db),
    redis: aioredis.Redis = Depends(deps.get_redis),
) -> Any:
    """
    Create new user.
    """
    user = crud.user.get_by_username_email_mobile(
        db, username=user_in.username, email=user_in.email, mobile=registration.mobile
    )
    if user is not None:
        raise HTTPException(
            status_code=400,
            detail="User with specified username, email or mobile exists in the system",
        )
    user_in = schemas.UserCreate(
        mobile=registration.mobile, **user_in.dict(exclude_unset=True)
    )
    user = await crud.user_cachedb.create(db, redis, obj_in=user_in)
    if settings.EMAILS_ENABLED and user_in.email:
        send_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )
    return user
