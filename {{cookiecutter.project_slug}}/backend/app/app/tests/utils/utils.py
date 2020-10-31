import random
import string
from typing import Dict

from sqlalchemy.orm import Session

from app import crud
from app.core import security
from app.core.config import settings


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


def random_mobile_number() -> str:
    return f"+989{random.randint(100000000, 999999999)}"


def get_user_token_headers_from_email(db: Session, *, email: str) -> Dict[str, str]:
    user = crud.user.get_by_email(db, email=email)
    token = security.create_access_token(user.id, is_verified=True)
    headers = {"Authorization": f"Bearer {token}"}
    return headers


def get_superuser_token_headers(db: Session) -> Dict[str, str]:
    return get_user_token_headers_from_email(db, email=settings.FIRST_SUPERUSER_EMAIL)


def get_normal_user_token_headers(db: Session) -> Dict[str, str]:
    return get_user_token_headers_from_email(db, email=settings.EMAIL_TEST_USER)
