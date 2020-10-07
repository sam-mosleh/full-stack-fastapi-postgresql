from typing import Dict

import socketio
from fastapi import HTTPException
from socketio.exceptions import ConnectionRefusedError

from app import schemas
from app.api import deps
from app.db.session import SessionLocal


class AuthenticatedNamespace(socketio.AsyncNamespace):
    async def on_connect(self, sid, environ):
        await self.authenticate_user(environ)

    async def authenticate_user(self, environ: Dict) -> schemas.UserInDB:
        token = environ.get("HTTP_AUTHORIZATION")
        if token is None:
            raise ConnectionRefusedError("Not authenticated")
        db = SessionLocal()
        try:
            return await deps.get_current_user(db, self.server.cache, token)
        except HTTPException as e:
            raise ConnectionRefusedError(e.detail)
        finally:
            db.close()
