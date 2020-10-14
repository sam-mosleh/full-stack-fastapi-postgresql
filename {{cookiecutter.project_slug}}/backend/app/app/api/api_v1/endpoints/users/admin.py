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
    skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db),
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


@router.get("/{id}", response_model=schemas.User)
async def read_user_by_id(
    user: schemas.UserInDB = Depends(deps.get_user_by_id),
) -> Any:
    """
    Get a specific user by id.
    """
    return user


@router.put("/{id}", response_model=schemas.User)
async def update_user(
    *,
    user: schemas.UserInDB = Depends(deps.get_user_by_id),
    user_in: schemas.UserUpdate,
    db: Session = Depends(deps.get_db),
    redis: aioredis.Redis = Depends(deps.get_redis),
) -> Any:
    """
    Update a user.
    """
    updated_user = await crud.user_cachedb.update(
        db, redis, cache_obj=user, obj_in=user_in
    )
    return updated_user
