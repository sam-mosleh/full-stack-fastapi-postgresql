from sqlalchemy.orm import Session

from app import crud
from app.models.item import Item
from app.models.user import User
from app.schemas.item import ItemCreate, ItemUpdate
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_lower_string


def test_create_item(db: Session, new_user: User) -> None:
    title = random_lower_string()
    description = random_lower_string()
    item_in = ItemCreate(title=title, description=description)
    item = crud.item.create_with_owner(db=db, obj_in=item_in, owner_id=new_user.id)
    assert item.title == title
    assert item.description == description
    assert item.owner_id == new_user.id


def test_get_item(db: Session, new_item: Item) -> None:
    stored_item = crud.item.get(db=db, id=new_item.id)
    assert stored_item
    assert new_item.id == stored_item.id
    assert new_item.title == stored_item.title
    assert new_item.description == stored_item.description
    assert new_item.owner_id == stored_item.owner_id


def test_update_item(db: Session, new_item: Item) -> None:
    description = random_lower_string()
    item_update = ItemUpdate(description=description)
    updated_item = crud.item.update(db=db, db_obj=new_item, obj_in=item_update)
    assert new_item.id == updated_item.id
    assert new_item.title == updated_item.title
    assert updated_item.description == description
    assert new_item.owner_id == updated_item.owner_id


def test_delete_item(db: Session) -> None:
    title = random_lower_string()
    description = random_lower_string()
    item_in = ItemCreate(title=title, description=description)
    user = create_random_user(db)
    item = crud.item.create_with_owner(db=db, obj_in=item_in, owner_id=user.id)
    item2 = crud.item.remove(db=db, id=item.id)
    item3 = crud.item.get(db=db, id=item.id)
    assert item3 is None
    assert item2.id == item.id
    assert item2.title == title
    assert item2.description == description
    assert item2.owner_id == user.id
