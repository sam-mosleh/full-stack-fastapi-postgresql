import uuid
from typing import Optional

import aioredis

from app.core.config import settings
from app.crud.base import CRUDCacheBase
from app.schemas.otp import OTPInDB
from app.schemas.registration import (
    RegistrationCreate,
    RegistrationInDB,
    RegistrationUpdate,
)


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

    async def set_otp(
        self, cache: aioredis.Redis, *, cache_obj: RegistrationInDB, otp: OTPInDB
    ):
        return await self.update(cache, cache_obj=cache_obj, obj_in={"otp_id": otp.id})

    async def verify_mobile(
        self, cache: aioredis.Redis, *, cache_obj: RegistrationInDB
    ):
        return await self.update(
            cache, cache_obj=cache_obj, obj_in={"mobile_is_verified": True}
        )


registration_cache = CRUDCacheRegistration(RegistrationInDB)
