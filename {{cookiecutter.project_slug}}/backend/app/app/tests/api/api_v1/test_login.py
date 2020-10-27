from typing import Dict

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, models, utils
from app.core.config import settings
from app.tests.utils.utils import random_lower_string


def test_get_access_token(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER_USERNAME,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    response = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = response.json()
    response.raise_for_status()
    assert "access_token" in tokens
    assert tokens["access_token"]


def test_use_access_token(
    client: TestClient, superuser_token_headers: Dict[str, str]
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/login/test-token", headers=superuser_token_headers,
    )
    result = response.json()
    response.raise_for_status()
    assert "email" in result


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
