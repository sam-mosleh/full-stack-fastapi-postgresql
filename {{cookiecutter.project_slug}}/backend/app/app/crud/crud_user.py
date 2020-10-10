from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase, CRUDCacheBase, CRUDCacheDBBase
from app.models.user import User
from app.schemas.user import UserCreate, UserInDB, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        obj_in_data = obj_in.dict(exclude={"password"})
        obj_in_data["hashed_password"] = get_password_hash(obj_in.password)
        db_obj = User(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(
        self, db: Session, *, username: str, password: str
    ) -> Optional[User]:
        user = self.get_by_username(db, username=username)
        if user is None:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


class CRUDCacheUser(CRUDCacheBase[UserInDB]):
    pass


class CRUDCacheDBUser(CRUDCacheDBBase[UserInDB, UserCreate, UserUpdate]):
    pass


user = CRUDUser(User)
user_cache = CRUDCacheUser(UserInDB, User.__tablename__)
user_cachedb = CRUDCacheDBUser(user, user_cache)
