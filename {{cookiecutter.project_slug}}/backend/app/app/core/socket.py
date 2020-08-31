import socketio

from app.core.config import settings

external_sio = socketio.AsyncRedisManager(settings.REDIS_DSN, write_only=True)
