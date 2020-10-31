import asyncio
from typing import Dict, Generator

import aioredis
import pytest
from async_asgi_testclient import TestClient as AsyncTestClient
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models.item import Item
from app.models.user import User
from app.tests.utils.item import create_random_item
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import (
    get_normal_user_token_headers,
    get_superuser_token_headers,
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db() -> Generator:
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(scope="session")
async def redis(event_loop) -> aioredis.Redis:
    cache = await aioredis.create_redis_pool(settings.APP_REDIS_DSN)
    yield cache
    cache.close()
    await cache.wait_closed()


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.mark.asyncio
@pytest.fixture(scope="module")
async def async_client() -> AsyncTestClient:
    async with AsyncTestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser(db: Session) -> User:
    return crud.user.get_by_username(db, username=settings.FIRST_SUPERUSER_USERNAME)


@pytest.fixture(scope="module")
def superuser_token_headers(db: Session) -> Dict[str, str]:
    return get_superuser_token_headers(db)


@pytest.fixture(scope="module")
def normal_user(db: Session) -> User:
    return crud.user.get_by_email(db, email=settings.EMAIL_TEST_USER)


@pytest.fixture(scope="module")
def normal_user_token_headers(db: Session) -> Dict[str, str]:
    # return authentication_token_from_email(
    #     client=client, email=settings.EMAIL_TEST_USER, db=db
    # )
    return get_normal_user_token_headers(db)


@pytest.fixture
def new_user(db: Session) -> User:
    return create_random_user(db)


@pytest.fixture
def new_item(db: Session, new_user: User) -> Item:
    return create_random_item(db, owner_id=new_user.id)
