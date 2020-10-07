from typing import Any

import socketio

from app.core.config import settings
from app.core.log import logger

from .base import AuthenticatedNamespace


class UserNamespace(AuthenticatedNamespace):
    def get_room(self, user_id: int) -> str:
        return f"user.{user_id}"

    async def emit_private(self, sio: socketio.AsyncManager, user_id: int, data: Any):
        await sio.emit(
            "private", data=data, room=self.get_room(user_id), namespace=self.namespace,
        )

    async def on_connect(self, sid, environ):
        user = await self.authenticate_user(environ)
        await self.save_session(sid, user)
        user_room = self.get_room(user.id)
        self.enter_room(sid, user_room)
        logger.info(f"User {user.id} ({user.full_name}) connected. Joined {user_room}")

    async def on_disconnect(self, sid):
        user = await self.get_session(sid)
        logger.info(f"User {user.id} ({user.full_name}) disconnected")


user_namespace = UserNamespace(settings.PUSHER_USER_NAMESPACE)
