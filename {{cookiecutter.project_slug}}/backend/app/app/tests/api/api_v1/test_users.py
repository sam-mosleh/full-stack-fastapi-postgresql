from typing import Dict

import pytest
from fastapi.testclient import TestClient
from requests.exceptions import HTTPError
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models.user import User
from app.tests.utils.utils import random_email, random_lower_string


def test_get_user_by_superuser(
    client: TestClient, superuser_token_headers: Dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers
    )
    current_user = response.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"]
    assert current_user["email"] == settings.FIRST_SUPERUSER_EMAIL


def test_get_user_by_normal_user(
    client: TestClient, normal_user_token_headers: Dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/users", headers=normal_user_token_headers
    )
    current_user = response.json()
    assert current_user
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is False
    assert current_user["email"] == settings.EMAIL_TEST_USER


def test_create_new_user_by_superuser(
    client: TestClient, superuser_token_headers: Dict[str, str], db: Session
) -> None:
    username = random_lower_string()
    email = random_email()
    password = random_lower_string()
    data = {"username": username, "email": email, "password": password}
    response = client.post(
        f"{settings.API_V1_STR}/admin/users/",
        headers=superuser_token_headers,
        json=data,
    )
    response.raise_for_status()
    created_user = response.json()
    user = crud.user.get_by_email(db, email=email)
    assert user
    assert user.username == created_user["username"]
    assert user.email == created_user["email"]


@pytest.mark.skipif(
    not settings.USERS_OPEN_REGISTRATION, reason="Open registration is provided"
)
def test_create_new_user_by_normal_user_with_open_registration(
    client: TestClient, db: Session
) -> None:
    username = random_lower_string()
    email = random_email()
    password = random_lower_string()
    data = {"username": username, "email": email, "password": password}
    response = client.post(f"{settings.API_V1_STR}/users/", json=data)
    response.raise_for_status()
    created_user = response.json()
    user = crud.user.get_by_email(db, email=email)
    assert user
    assert user.username == created_user["username"]
    assert user.email == created_user["email"]


@pytest.mark.skipif(
    settings.USERS_OPEN_REGISTRATION, reason="Open registration is not provided"
)
def test_create_new_user_by_normal_user_without_open_registration(
    client: TestClient, db: Session
) -> None:
    username = random_lower_string()
    email = random_email()
    password = random_lower_string()
    data = {"username": username, "email": email, "password": password}
    response = client.post(f"{settings.API_V1_STR}/users/", json=data)
    with pytest.raises(HTTPError):
        response.raise_for_status()
    content = response.json()
    assert "id" not in content


def test_get_existing_user_by_superuser(
    client: TestClient,
    superuser_token_headers: Dict[str, str],
    db: Session,
    new_user: User,
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/admin/users/{new_user.id}",
        headers=superuser_token_headers,
    )
    response.raise_for_status()
    api_user = response.json()
    assert new_user.username == api_user["username"]
    assert new_user.email == api_user["email"]


def test_get_existing_user_by_normal_user(
    client: TestClient,
    normal_user_token_headers: Dict[str, str],
    db: Session,
    new_user: User,
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/admin/users/{new_user.id}",
        headers=normal_user_token_headers,
    )
    with pytest.raises(HTTPError):
        response.raise_for_status()
    content = response.json()
    assert "id" not in content


def test_create_user_existing_username_by_superuser(
    client: TestClient,
    superuser_token_headers: Dict[str, str],
    db: Session,
    new_user: User,
) -> None:
    password = random_lower_string()
    data = {
        "username": new_user.email,
        "email": new_user.email,
        "password": password,
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/users/",
        headers=superuser_token_headers,
        json=data,
    )
    with pytest.raises(HTTPError):
        response.raise_for_status()
    content = response.json()
    assert "id" not in content


def test_create_admin_user_by_normal_user(
    client: TestClient, normal_user_token_headers: Dict[str, str]
) -> None:
    username = random_lower_string()
    email = random_email()
    password = random_lower_string()
    data = {
        "username": username,
        "email": email,
        "password": password,
        "is_superuser": True,
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/users/",
        headers=normal_user_token_headers,
        json=data,
    )
    with pytest.raises(HTTPError):
        response.raise_for_status()
    content = response.json()
    assert "id" not in content


def test_retrieve_users(
    client: TestClient, superuser_token_headers: Dict[str, str], new_user: User
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/admin/users/", headers=superuser_token_headers,
    )
    response.raise_for_status()
    all_users = response.json()
    assert len(all_users) >= 2
    for user in all_users:
        assert "id" in user
        assert "username" in user
        assert "email" in user
        assert "password" not in user
        assert "hashed_password" not in user
