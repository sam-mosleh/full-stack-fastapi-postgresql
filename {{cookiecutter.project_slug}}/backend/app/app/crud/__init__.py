from .crud_item import item
from .crud_user import user, user_cache, user_cachedb
from .crud_otp import otp_cache
from .crud_registration import registration_cache

# For a new basic set of CRUD operations you could just do

# from .base import CRUDBase
# from app.models.item import Item
# from app.schemas.item import ItemCreate, ItemUpdate

# item = CRUDBase[Item, ItemCreate, ItemUpdate](Item)
