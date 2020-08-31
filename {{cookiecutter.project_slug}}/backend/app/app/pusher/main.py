import socketio

from app.core.config import settings
from app.core.log import logger
from app.pusher.namespaces import root_namespace, user_namespace

mgr = socketio.AsyncRedisManager(settings.REDIS_DSN)
sio = socketio.AsyncServer(async_mode="asgi", client_manager=mgr, logger=logger)

sio.register_namespace(root_namespace)
sio.register_namespace(user_namespace)

app = socketio.ASGIApp(sio)
