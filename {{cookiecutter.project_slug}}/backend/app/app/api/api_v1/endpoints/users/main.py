from typing import Any

import aioredis
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.api.api_v1.endpoints.users import registrations

router = APIRouter()


@router.put("/", response_model=schemas.User)
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


@router.get("/", response_model=schemas.User)
def read_user_me(
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserInDB = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


router.include_router(
    registrations.router, prefix="/registrations", tags=["registrations"]
)
