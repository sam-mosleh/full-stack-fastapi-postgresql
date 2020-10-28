import uuid
from typing import Optional

import aioredis

from app.core.config import settings
from app.crud.base import CRUDCacheBase
from app.schemas.otp import OTPCreate, OTPInDB


class CRUDCacheOTP(CRUDCacheBase[OTPInDB, OTPCreate, OTPInDB]):
    async def create(
        self,
        cache: aioredis.Redis,
        *,
        obj_in: OTPCreate,
        id: Optional[uuid.UUID] = None,
    ) -> OTPInDB:
        obj_in = {
            "id": id or uuid.uuid4(),
            "valid_for": settings.OTP_EXPIRE_SECONDS,
            **obj_in.dict(),
        }
        return await self.add_dict(
            cache, obj_in=obj_in, expire=settings.OTP_EXPIRE_SECONDS
        )


otp_cache = CRUDCacheOTP(OTPInDB)
