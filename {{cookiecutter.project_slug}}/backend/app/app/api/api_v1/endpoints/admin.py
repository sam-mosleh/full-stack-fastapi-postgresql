from fastapi import APIRouter

from app.api.api_v1.endpoints import users

router = APIRouter()

router.include_router(
    users.admin.router, prefix="/users", tags=["users"],
)
