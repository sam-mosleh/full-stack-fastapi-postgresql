from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app import crud
from app.core.security import verify_password
from app.models import User
from app.schemas.user import UserCreate, UserUpdate
from app.tests.utils.utils import random_email, random_lower_string


def test_create_user(db: Session) -> None:
    username = random_lower_string()
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(username=username, email=email, password=password)
    user = crud.user.create(db, obj_in=user_in)
    assert user.username == username
    assert user.email == email
    assert hasattr(user, "hashed_password")


def test_authenticate_user(db: Session) -> None:
    username = random_lower_string()
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(username=username, email=email, password=password)
    user = crud.user.create(db, obj_in=user_in)
    authenticated_user = crud.user.authenticate(
        db, username=username, password=password
    )
    assert authenticated_user
    assert user.username == authenticated_user.username
    assert user.email == authenticated_user.email


def test_not_authenticate_user(db: Session) -> None:
    username = random_lower_string()
    password = random_lower_string()
    user = crud.user.authenticate(db, username=username, password=password)
    assert user is None


def test_check_if_user_is_active(new_user: User) -> None:
    assert new_user.is_active


def test_check_if_user_is_inactive(db: Session) -> None:
    username = random_lower_string()
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(
        username=username, email=email, password=password, is_active=False
    )
    user = crud.user.create(db, obj_in=user_in)
    assert not user.is_active


def test_check_if_user_is_superuser(db: Session) -> None:
    username = random_lower_string()
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(
        username=username, email=email, password=password, is_superuser=True
    )
    user = crud.user.create(db, obj_in=user_in)
    assert user.is_superuser


def test_check_if_user_is_normal_user(new_user: User) -> None:
    assert not new_user.is_superuser


def test_get_user(db: Session, new_user: User) -> None:
    user = crud.user.get(db, id=new_user.id)
    assert user
    assert user.username == new_user.username
    assert user.email == new_user.email
    assert jsonable_encoder(user) == jsonable_encoder(new_user)


def test_update_user(db: Session, new_user: User) -> None:
    new_password = random_lower_string()
    user_in_update = UserUpdate(password=new_password, is_superuser=True)
    crud.user.update(db, db_obj=new_user, obj_in=user_in_update)
    user = crud.user.get(db, id=new_user.id)
    assert user
    assert user.username == new_user.username
    assert user.email == new_user.email
    assert verify_password(new_password, user.hashed_password)
