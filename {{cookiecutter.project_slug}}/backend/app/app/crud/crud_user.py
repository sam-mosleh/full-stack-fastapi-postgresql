from typing import Any, Dict, Optional, Union

import aioredis
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase, CRUDCacheBase, CRUDDBCacheBase
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
        return self.create_dict(db, create_data=obj_in_data)

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"]
        return self.update_dict(db, db_obj=db_obj, update_data=update_data)

    def authenticate(
        self, db: Session, *, username: str, password: str
    ) -> Optional[User]:
        user = self.get_by_username(db, username=username)
        if user is None:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


class CRUDCacheUser(CRUDCacheBase[UserInDB, UserCreate, UserUpdate]):
    pass


class CRUDDBCacheUser(CRUDDBCacheBase[User, UserInDB, UserCreate, UserUpdate]):
    async def get_by_username(
        self, db: Session, cache: aioredis.Redis, *, username: str
    ) -> Optional[UserInDB]:
        user = self.crud_db.get_by_username(db, username=username)
        if user is None:
            return None
        return await self.crud_cache.get(cache, id=user.id)

    async def get_by_email(
        self, db: Session, cache: aioredis.Redis, *, email: str
    ) -> Optional[UserInDB]:
        user = self.crud_db.get_by_email(db, email=email)
        if user is None:
            return None
        return await self.crud_cache.get(cache, id=user.id)

    async def authenticate(
        self, db: Session, cache: aioredis.Redis, *, username: str, password: str
    ) -> Optional[UserInDB]:
        user = await self.get_by_username(db, cache, username=username)
        if user is None:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


user = CRUDUser(User)
user_cache = CRUDCacheUser(UserInDB, User.__tablename__)
user_cachedb = CRUDDBCacheUser(user, user_cache, expire=3600)
