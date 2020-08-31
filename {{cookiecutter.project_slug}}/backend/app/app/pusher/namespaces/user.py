from typing import Any

from app.core.config import settings
from app.core.log import logger

from .base import AuthenticatedNamespace


def get_room(user_id: int):
    return f"user.{user_id}"


async def emit_user(sio, user_id: int, data: Any):
    return await sio.emit(
        "private",
        data=data,
        room=get_room(user_id),
        namespace=settings.PUSHER_USER_NAMESPACE,
    )


class UserNamespace(AuthenticatedNamespace):
    async def on_connect(self, sid, environ):
        user = await self.authenticate_user(environ)
        await self.save_session(sid, user)
        user_room = get_room(user["id"])
        self.enter_room(sid, user_room)
        logger.info(
            f"User {user['id']} ({user['full_name']}) connected. Joined {user_room}"
        )

    async def on_disconnect(self, sid):
        user = await self.get_session(sid)
        logger.info(f"User {user['id']} ({user['full_name']}) disconnected")


user_namespace = UserNamespace(settings.PUSHER_USER_NAMESPACE)
