import asyncio

import aiohttp

from app.core.config import settings


class SmsIrClient:
    token_uri: str = "/api/Token"
    fast_send_uri: str = "/api/UltraFastSend"

    def __init__(
        self, api_key: str, secret_key: str, base_url: str = "https://RestfulSms.com"
    ):
        self._api_key = api_key
        self._secret_key = secret_key
        self.base_url = base_url
        self._token = None

    async def __aenter__(self):
        await self.start()

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def start(self):
        self.session = aiohttp.ClientSession()
        self._token = await self.get_token()
        self._updater_task = asyncio.create_task(self.token_updater())

    async def close(self):
        await self.session.close()

    async def token_updater(self):
        while True:
            await asyncio.sleep(settings.SMS_UPDATE_TOKEN_INTERVAL)
            self._token = await self.get_token()

    async def get_token(self) -> str:
        url = f"{self.base_url}{self.token_uri}"
        body = {"UserApiKey": self._api_key, "SecretKey": self._secret_key}
        async with self.session.post(url, json=body) as response:
            response_json = await response.json()
            if response_json["IsSuccessful"] is False:
                raise Exception(f"Token fetching failed: {response['Message']}")
            return response_json["TokenKey"]

    async def send(self, mobile_no: str, template_id: int, params: dict = {}) -> int:
        if self._token is None:
            raise ValueError("Token is not set")
        url = f"{self.base_url}{self.fast_send_uri}"
        headers = {"x-sms-ir-secure-token": self._token}
        body = {
            "ParameterArray": [
                {"Parameter": key, "ParameterValue": value}
                for key, value in params.items()
            ],
            "Mobile": mobile_no,
            "TemplateId": template_id,
        }
        async with self.session.post(url, json=body, headers=headers) as response:
            response_json = await response.json()
            if response_json["IsSuccessful"] is False:
                raise Exception(f"SMS sending failed: {response_json['Message']}")
            return int(response_json["VerificationCodeId"])


sms_client = SmsIrClient(settings.SMS_API_KEY, settings.SMS_SECRET_KEY)
