from typing import Dict

import aiohttp
import socketio
from socketio.exceptions import ConnectionRefusedError

from app.core.config import settings


class AuthenticatedNamespace(socketio.AsyncNamespace):
    async def on_connect(self, sid, environ):
        await self.authenticate_user(environ)

    async def authenticate_user(self, environ: Dict):
        headers = {
            "Authorization": environ.get("HTTP_AUTHORIZATION"),
            "accept": "application/json",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(settings.TEST_TOKEN_URL) as response:
                response_json = await response.json()
                if response.status >= 400:
                    raise ConnectionRefusedError(response_json)
                return response_json
