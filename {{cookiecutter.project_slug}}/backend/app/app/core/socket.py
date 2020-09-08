import socketio

from app.core.config import settings
from app.core.log import logger

external_sio = socketio.AsyncRedisManager(
    settings.REDIS_DSN, write_only=True, logger=logger
)
