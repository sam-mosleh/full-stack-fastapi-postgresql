from typing import Dict, Tuple

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.tests.utils.utils import (
    random_email,
    random_lower_string,
    random_mobile_number,
)


def user_authentication_headers(
    *, client: TestClient, username: str, password: str
) -> Dict[str, str]:
    data = {"username": username, "password": password}

    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def create_random_user(db: Session) -> User:
    username = random_lower_string()
    email = random_email()
    mobile = random_mobile_number()
    password = random_lower_string()
    user_in = UserCreate(
        username=username, email=email, mobile=mobile, password=password
    )
    user = crud.user.create(db=db, obj_in=user_in)
    return user


def create_random_user_password_tuple(db: Session) -> Tuple[User, str]:
    username = random_lower_string()
    email = random_email()
    mobile = random_mobile_number()
    password = random_lower_string()
    user_in = UserCreate(
        username=username, email=email, mobile=mobile, password=password
    )
    user = crud.user.create(db=db, obj_in=user_in)
    return user, password


def authentication_token_from_email(
    *, client: TestClient, email: str, db: Session
) -> Dict[str, str]:
    """
    Return a valid token for the user with given email.

    If the user doesn't exist it is created first.
    """
    username = random_lower_string()
    mobile = random_mobile_number()
    password = random_lower_string()
    user = crud.user.get_by_email(db, email=email)
    if not user:
        user_in_create = UserCreate(
            username=username, email=email, mobile=mobile, password=password
        )
        user = crud.user.create(db, obj_in=user_in_create)
    else:
        user_in_update = UserUpdate(username=username, mobile=mobile, password=password)
        user = crud.user.update(db, db_obj=user, obj_in=user_in_update)

    return user_authentication_headers(
        client=client, username=username, password=password
    )
