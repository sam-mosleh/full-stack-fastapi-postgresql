from typing import Any, List

import aioredis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.core.config import settings
from app.utils import send_new_account_email

router = APIRouter()


@router.get("/", response_model=List[schemas.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserInDB = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Retrieve users.
    """
    return crud.user.get_multi(db, skip=skip, limit=limit)


@router.post("/", response_model=schemas.User)
async def create_user(
    *,
    user_in: schemas.UserCreate,
    db: Session = Depends(deps.get_db),
    redis: aioredis.Redis = Depends(deps.get_redis),
    current_user: schemas.UserInDB = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new user.
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = await crud.user_cachedb.create(db, redis, obj_in=user_in)
    if settings.EMAILS_ENABLED:
        send_new_account_email(
            email_to=user.email, username=user.username, password=user_in.password
        )
    return user


@router.put("/me", response_model=schemas.User)
async def update_user_me(
    *,
    user_in: schemas.UnprivilegedUserUpdate,
    db: Session = Depends(deps.get_db),
    redis: aioredis.Redis = Depends(deps.get_redis),
    current_user: schemas.UserInDB = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    user_in = schemas.UserUpdate(**user_in.dict(exclude_unset=True))
    return await crud.user_cachedb.update(
        db, redis, cache_obj=current_user, obj_in=user_in
    )


@router.get("/me", response_model=schemas.User)
def read_user_me(
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserInDB = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.post("/open", response_model=schemas.User)
async def create_user_open(
    *,
    user_in: schemas.UnprivilegedUserCreate,
    db: Session = Depends(deps.get_db),
    redis: aioredis.Redis = Depends(deps.get_redis),
) -> Any:
    """
    Create new user without the need to be logged in.
    """
    if not settings.USERS_OPEN_REGISTRATION:
        raise HTTPException(
            status_code=403,
            detail="Open user registration is forbidden on this server",
        )
    user = crud.user.get_by_email(db, email=user_in.email)
    if user is not None:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system",
        )
    user_in = schemas.UserCreate(user_in.dict(exclude_unset=True))
    user = await crud.user_cachedb.create(db, redis, obj_in=user_in)
    if settings.EMAILS_ENABLED and user_in.email:
        send_new_account_email(
            email_to=user_in.email, username=user_in.email, password=user_in.password
        )


@router.get("/{user_id}", response_model=schemas.User)
async def read_user_by_id(
    user_id: int,
    db: Session = Depends(deps.get_db),
    redis: aioredis.Redis = Depends(deps.get_redis),
    current_user: schemas.UserInDB = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get a specific user by id.
    """
    user = await crud.user_cachedb.get(db, redis, id=user_id)
    if user != current_user and not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return user


@router.put("/{user_id}", response_model=schemas.User)
async def update_user(
    *,
    user_id: int,
    user_in: schemas.UserUpdate,
    db: Session = Depends(deps.get_db),
    redis: aioredis.Redis = Depends(deps.get_redis),
    current_user: schemas.UserInDB = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a user.
    """
    user = await crud.user_cachedb.get(db, redis, id=user_id)
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system",
        )
    user = await crud.user_cachedb.update(db, redis, cache_obj=user, obj_in=user_in)
    return user
