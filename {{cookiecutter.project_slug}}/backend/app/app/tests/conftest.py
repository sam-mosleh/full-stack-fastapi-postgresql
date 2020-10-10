from typing import Dict, Generator

import aioredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models.user import User
from app.schemas.user import UserCreate
from app.tests.utils.user import authentication_token_from_email
from app.tests.utils.utils import (
    get_superuser_token_headers,
    random_email,
    random_lower_string,
)


@pytest.fixture(scope="session")
def db() -> Generator:
    yield SessionLocal()


@pytest.fixture(scope="module")
async def redis() -> aioredis.Redis:
    cache = await aioredis.create_redis_pool(settings.APP_REDIS_DSN)
    yield cache
    cache.close()
    await cache.wait_closed()


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> Dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> Dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


@pytest.fixture
def new_user(db: Session) -> User:
    username = random_lower_string()
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(username=username, email=email, password=password)
    return crud.user.create(db, obj_in=user_in)
