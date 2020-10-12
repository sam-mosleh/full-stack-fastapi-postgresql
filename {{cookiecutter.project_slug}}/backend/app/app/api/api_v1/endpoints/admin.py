import uuid
from typing import Any, List

import aioredis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.core.config import settings
from app.utils import send_new_account_email
from app.api.api_v1.endpoints import users

router = APIRouter()

router.include_router(
    users.admin.router, prefix="/users", tags=["users"],
)

