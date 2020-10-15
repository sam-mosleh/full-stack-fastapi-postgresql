from fastapi import APIRouter

from app.api.api_v1.endpoints import items, users

router = APIRouter()

router.include_router(
    users.admin.router, prefix="/users", tags=["users"],
)
router.include_router(
    items.admin.router, prefix="/items", tags=["items"],
)
