from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.db.types import GUID

if TYPE_CHECKING:
    from .item import Item  # noqa: F401


class User(Base):
    id = Column(GUID, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    mobile = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean())
    is_superuser = Column(Boolean())
    items = relationship("Item", back_populates="owner")
