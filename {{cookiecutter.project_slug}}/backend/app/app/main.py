import aioredis
import aioredlock
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.api_v1.api import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def on_startup() -> None:
    app.state.redis = await aioredis.create_redis_pool(settings.APP_REDIS_DSN)
    app.state.lock = aioredlock.Aioredlock([app.state.redis])


@app.on_event("shutdown")
async def on_shutdown() -> None:
    app.state.redis.close()
    await app.state.redis.wait_closed()
    await app.state.lock.destroy()
