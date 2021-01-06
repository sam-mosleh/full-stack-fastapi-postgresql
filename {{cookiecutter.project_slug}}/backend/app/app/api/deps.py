from typing import Generator, Optional

import aioredis
import aioredlock
import starlette
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core import security
from app.core.config import settings
from app.db.session import SessionLocal

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=settings.ACCESS_TOKEN_URL)


def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_redis(request: starlette.requests.Request) -> aioredis.Redis:
    return request.app.state.redis


def get_lock(request: starlette.requests.Request) -> aioredlock.Aioredlock:
    return request.app.state.lock


async def get_current_user(
    db: Session = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    token: str = Depends(reusable_oauth2),
) -> schemas.UserInDB:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = await crud.user_cachedb.get(db, redis, id=token_data.sub)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_current_active_user(
    current_user: schemas.UserInDB = Depends(get_current_user),
) -> schemas.UserInDB:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_superuser(
    current_user: schemas.UserInDB = Depends(get_current_active_user),
) -> schemas.UserInDB:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


async def get_user_by_id(
    id: int, db: Session = Depends(get_db), redis: aioredis.Redis = Depends(get_redis),
) -> schemas.UserInDB:
    user = await crud.user_cachedb.get(db, redis, id=id)
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    return user


async def get_owner_by_id(
    owner_id: Optional[int] = None,
    db: Session = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> Optional[schemas.UserInDB]:
    if owner_id is None:
        return None
    user = await crud.user_cachedb.get(db, redis, id=owner_id)
    if user is None:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    return user


def get_item_by_id(id: int, db: Session = Depends(get_db),) -> models.Item:
    item = crud.item.get(db=db, id=id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


def get_owned_item_by_id(
    item: models.Item = Depends(get_item_by_id),
    current_user: schemas.UserInDB = Depends(get_current_active_user),
) -> models.Item:
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
