from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
import asyncio
from aioredis import Redis
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        # obj_in_data = jsonable_encoder(obj_in)
        # return self.create_dict(db, create_data=obj_in_data)
        return self.create_dict(db, create_data=obj_in.dict())

    def create_dict(self, db: Session, *, create_data: Dict[str, Any]) -> ModelType:
        db_obj = self.model(**create_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        return self.update_dict(db, db_obj=db_obj, update_data=update_data)

    def update_dict(
        self, db: Session, *, db_obj: ModelType, update_data: Dict[str, Any],
    ) -> ModelType:
        obj_data = jsonable_encoder(db_obj)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj


class OrmMode(BaseModel):
    id: Any

    class Config:
        orm_mode = True


CacheSchemaType = TypeVar("CacheSchemaType", bound=OrmMode)


class CRUDCacheBase(Generic[CacheSchemaType, CreateSchemaType, UpdateSchemaType]):
    def __init__(
        self,
        schema: Type[CacheSchemaType],
        tablename: Optional[str] = None,
        change_limit: int = 1,
    ):
        self.schema = schema
        self.tablename = tablename if tablename is not None else schema.__name__.lower()
        self.change_limit = change_limit

    def build(self, data: Any) -> CacheSchemaType:
        return self.schema.from_orm(data)

    def to_key(self, id: Union[int, str]) -> str:
        return f"{self.tablename}:{id}"

    def to_change_list_key(self, id: Union[int, str]) -> str:
        return f"{self.to_key(id)}:changes"

    async def exists(self, cache: Redis, *, id: Any) -> bool:
        return await cache.exists(self.to_key(id))

    async def add(
        self, cache: Redis, *, obj_in: CacheSchemaType, expire: Optional[int] = None,
    ) -> CacheSchemaType:
        record_key = self.to_key(obj_in.id)
        await cache.set(record_key, obj_in.json(), expire=expire)
        return obj_in

    async def add_dict(
        self, cache: Redis, *, obj_in: Dict[str, Any], expire: Optional[int] = None,
    ) -> CacheSchemaType:
        record = self.schema(**obj_in)
        return await self.add(cache, obj_in=record, expire=expire)

    async def add_changes(
        self, cache: Redis, *, obj: CacheSchemaType
    ) -> CacheSchemaType:
        change_list_key = self.to_change_list_key(obj.id)
        await cache.lpush(change_list_key, obj.json())
        await cache.ltrim(change_list_key, 0, self.change_limit - 1)
        return obj

    async def get(self, cache: Redis, *, id: Any) -> Optional[CacheSchemaType]:
        result = await cache.get(self.to_key(id), encoding="utf-8")
        return self.schema.parse_raw(result) if result is not None else None

    async def get_changes(
        self, cache: Redis, *, id: Any, limit: int = 1000
    ) -> List[CacheSchemaType]:
        change_list_key = self.to_change_list_key(id)
        json_list = await cache.lrange(change_list_key, 0, limit - 1, encoding="utf-8")
        return [self.schema.parse_raw(record) for record in json_list]

    async def add_model(
        self, cache: Redis, *, obj_in: Any, expire: Optional[int] = None,
    ) -> CacheSchemaType:
        return await self.add(cache, obj_in=self.build(obj_in), expire=expire)

    async def create(
        self, cache: Redis, *, obj_in: CreateSchemaType, expire: Optional[int] = None,
    ) -> CacheSchemaType:
        return await self.add_dict(cache, obj_in=obj_in.dict(), expire=expire)

    async def update(
        self,
        cache: Redis,
        *,
        cache_obj: CacheSchemaType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
        expire: Optional[int] = None,
    ) -> CacheSchemaType:
        data = cache_obj.dict()
        if isinstance(obj_in, dict):
            data.update(obj_in)
        else:
            data.update(obj_in.dict(exclude_unset=True))
        return await self.add_dict(cache, obj_in=data, expire=expire)

    async def remove(self, cache: Redis, *, id: Any) -> Optional[CacheSchemaType]:
        record = await self.get(cache=cache, id=id)
        if record is not None:
            await cache.delete(self.to_key(id))
            return record
        else:
            return None


class CRUDCacheDBBase(Generic[CacheSchemaType, CreateSchemaType, UpdateSchemaType]):
    def __init__(
        self, crud_db: CRUDBase, crud_cache: CRUDCacheBase,
    ):
        self.crud_db = crud_db
        self.crud_cache = crud_cache

    async def get(
        self, db: Session, cache: Redis, *, id: Any
    ) -> Optional[CacheSchemaType]:
        result = await self.crud_cache.get(cache=cache, id=id)
        if result is None:
            search_result = self.crud_db.get(db, id)
            if search_result is not None:
                result = await self.crud_cache.add_model(cache, obj_in=search_result)
        return result

    async def load(
        self, db: Session, cache: Redis, *, limit: Optional[int] = 1000
    ) -> List[CacheSchemaType]:
        records = self.crud_db.get_multi(db, limit=limit)
        coros = []
        for record in records:
            exists = await self.crud_cache.exists(cache=cache, id=record.id)
            if not exists:
                coros.append(self.crud_cache.add_model(cache, obj_in=record))
        return await asyncio.gather(*coros)

    async def create(
        self, db: Session, cache: Redis, *, obj_in: CreateSchemaType
    ) -> CacheSchemaType:
        obj_data = obj_in.dict()
        return await self.create_dict(db, cache, obj_in=obj_data)

    async def create_dict(
        self, db: Session, cache: Redis, *, obj_in: Dict[str, Any]
    ) -> CacheSchemaType:
        result = await self.crud_cache.add_dict(cache, obj_in=obj_in)
        self.crud_db.create_dict(db, create_data=obj_in)
        return result

    async def update(
        self,
        db: Session,
        cache: Redis,
        *,
        cache_obj: CacheSchemaType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> CacheSchemaType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        return await self.update_dict(
            db, cache, cache_obj=cache_obj, obj_in=update_data
        )

    async def update_dict(
        self,
        db: Session,
        cache: Redis,
        *,
        cache_obj: CacheSchemaType,
        obj_in: Dict[str, Any],
    ) -> CacheSchemaType:
        data = cache_obj.dict()
        data.update(obj_in)
        result = await self.crud_cache.add_dict(cache, obj_in=data)
        model = self.crud_db.get(db, cache_obj.id)
        self.crud_db.update_dict(db, db_obj=model, update_data=obj_in)
        return result

    async def remove(self, db: Session, cache: Redis, *, id: Any) -> CacheSchemaType:
        await self.crud_cache.remove(cache=cache, id=id)
        model = self.crud_db.remove(db, id=id)
        return self.crud_cache.schema.from_orm(model)
