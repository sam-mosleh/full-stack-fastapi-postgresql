import aioredis
import socketio

from app.core.config import settings
from app.core.log import logger
from app.pusher.namespaces import root_namespace, user_namespace

mgr = socketio.AsyncRedisManager(settings.REDIS_DSN)
sio = socketio.AsyncServer(async_mode="asgi", client_manager=mgr, logger=logger)

sio.register_namespace(root_namespace)
sio.register_namespace(user_namespace)


async def on_startup():
    sio.cache = await aioredis.create_redis_pool(settings.REDIS_DSN)


async def on_shutdown():
    sio.cache.close()
    await sio.cache.wait_closed()


app = socketio.ASGIApp(sio, on_startup=on_startup, on_shutdown=on_shutdown)
