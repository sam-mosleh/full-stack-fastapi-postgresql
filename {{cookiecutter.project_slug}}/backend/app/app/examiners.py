import logging

import aioredis
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

from app.core.config import settings
from app.db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def check_db() -> None:
    try:
        # Try to create session to check if DB is awake
        db = SessionLocal()
        db.execute("SELECT 1")
    except Exception:
        logger.exception("Init failed")
        raise


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
async def check_cache() -> None:
    try:
        # Try to create pool to check if Redis is awake
        cache = await aioredis.create_redis_pool(settings.APP_REDIS_DSN)
        await cache.get("")
    except Exception:
        logger.exception("Init failed")
        raise
