from typing import Dict

import aioredis
import pytest
from async_asgi_testclient import TestClient as AsyncTestClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, models, utils
from app.core.config import settings
from app.tests.utils.user import create_random_user_password_tuple
from app.tests.utils.utils import random_lower_string


@pytest.fixture
def new_user_otp_token(client: TestClient, db: Session) -> str:
    user, password = create_random_user_password_tuple(db)
    data = {"username": user.username, "password": password}
    response = client.post(f"{settings.API_V1_STR}/login/otp/token", json=data)
    result = response.json()
    return result["otp_token"]


@pytest.mark.asyncio
@pytest.fixture
async def new_user_access_token(
    new_user_otp_token: str, redis: aioredis.Redis, async_client: AsyncTestClient
) -> str:
    data = {"otp_token": new_user_otp_token}
    response = await async_client.post(
        f"{settings.API_V1_STR}/login/otp/send", json=data
    )
    result = response.json()
    otp = await crud.otp_cache.get(redis, id=result["id"])
    data = {"otp_token": new_user_otp_token, "code": otp.verification_code}
    response = await async_client.post(
        f"{settings.API_V1_STR}/login/access-token", json=data
    )
    result = response.json()
    return result["access_token"]


@pytest.mark.asyncio
async def test_create_access_token(
    new_user_otp_token: str, redis: aioredis.Redis, async_client: AsyncTestClient
):
    data = {"otp_token": new_user_otp_token}
    response = await async_client.post(
        f"{settings.API_V1_STR}/login/otp/send", json=data
    )
    response.raise_for_status()
    result = response.json()
    otp = await crud.otp_cache.get(redis, id=result["id"])
    data = {"otp_token": new_user_otp_token, "code": otp.verification_code}
    response = await async_client.post(
        f"{settings.API_V1_STR}/login/access-token", json=data
    )
    response.raise_for_status()
    result = response.json()
    assert "access_token" in result
    assert result["access_token"]


def test_get_otp_token(redis: aioredis.Redis, client: TestClient) -> None:
    data = {
        "username": settings.FIRST_SUPERUSER_USERNAME,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }

    response = client.post(f"{settings.API_V1_STR}/login/otp/token", json=data)
    response.raise_for_status()
    result = response.json()
    assert "otp_token" in result
    assert result["otp_token"]

    # response = client.post(
    #     f"{settings.API_V1_STR}/login/test-token",
    #     headers={"Authorization": f"Bearer {token}"},
    # )
    # result = response.json()
    # response.raise_for_status()
    # assert "email" in result


@pytest.mark.asyncio
async def test_send_otp(
    new_user_otp_token: str, redis: aioredis.Redis, async_client: AsyncTestClient
):
    data = {"otp_token": new_user_otp_token}
    response = await async_client.post(
        f"{settings.API_V1_STR}/login/otp/send", json=data
    )
    result = response.json()
    response.raise_for_status()
    assert "id" in result
    otp = await crud.otp_cache.get(redis, id=result["id"])
    assert otp


@pytest.mark.asyncio
async def test_send_otp_doesnt_show_user_mobile(
    new_user_otp_token: str, redis: aioredis.Redis, async_client: AsyncTestClient
):
    data = {"otp_token": new_user_otp_token}
    response = await async_client.post(
        f"{settings.API_V1_STR}/login/otp/send", json=data
    )
    response.raise_for_status()
    result = response.json()
    otp = await crud.otp_cache.get(redis, id=result["id"])
    assert otp.mobile != result["mobile"]


@pytest.mark.asyncio
async def test_create_access_token(
    new_user_otp_token: str, redis: aioredis.Redis, async_client: AsyncTestClient
):
    data = {"otp_token": new_user_otp_token}
    response = await async_client.post(
        f"{settings.API_V1_STR}/login/otp/send", json=data
    )
    response.raise_for_status()
    result = response.json()
    otp = await crud.otp_cache.get(redis, id=result["id"])
    data = {"otp_token": new_user_otp_token, "code": otp.verification_code}
    response = await async_client.post(
        f"{settings.API_V1_STR}/login/access-token", json=data
    )
    response.raise_for_status()
    result = response.json()
    assert "access_token" in result
    assert result["access_token"]


def test_use_new_user_access_token(
    client: TestClient, new_user_access_token: str
) -> None:
    new_user_token_headers = {"Authorization": f"Bearer {new_user_access_token}"}
    response = client.post(
        f"{settings.API_V1_STR}/login/test-token", headers=new_user_token_headers,
    )
    result = response.json()
    response.raise_for_status()
    assert "id" in result


def test_use_access_token(
    client: TestClient, superuser_token_headers: Dict[str, str]
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/login/test-token", headers=superuser_token_headers,
    )
    result = response.json()
    response.raise_for_status()
    assert "id" in result


def test_reset_password(client: TestClient, db: Session, normal_user: models.User):
    token = utils.generate_password_reset_token(normal_user.email)
    new_password = random_lower_string()
    reset_password_data = {"token": token, "new_password": new_password}
    response = client.post(
        f"{settings.API_V1_STR}/reset-password", json=reset_password_data
    )
    response.raise_for_status()
    db.refresh(normal_user)
    user = crud.user.authenticate(
        db, username=normal_user.username, password=new_password
    )
    assert user
