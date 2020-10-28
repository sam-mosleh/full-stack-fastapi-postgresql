import uuid
from typing import Any, Dict, Optional, Union

import aioredis
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase, CRUDCacheBase, CRUDCacheDBBase
from app.schemas.registration import (
    RegistrationInDB,
    RegistrationCreate,
    RegistrationUpdate,
)

from app.core.config import settings


class CRUDCacheRegistration(
    CRUDCacheBase[RegistrationInDB, RegistrationCreate, RegistrationUpdate]
):
    async def create(
        self,
        cache: aioredis.Redis,
        *,
        obj_in: RegistrationCreate,
        id: Optional[uuid.UUID] = None,
    ) -> RegistrationInDB:
        obj_in = {
            "id": id or uuid.uuid4(),
            "valid_for": settings.REGISTRATION_EXPIRE_SECONDS,
            **obj_in.dict(),
        }
        return await self.add_dict(
            cache, obj_in=obj_in, expire=settings.REGISTRATION_EXPIRE_SECONDS
        )


registration_cache = CRUDCacheRegistration(RegistrationInDB)
