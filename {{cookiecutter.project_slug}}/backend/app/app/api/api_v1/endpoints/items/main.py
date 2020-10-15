from typing import Any, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.Item])
def read_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserInDB = Depends(deps.get_current_active_user),
) -> Any:
    """
    Retrieve user items.
    """
    items = crud.item.get_multi_by_owner(
        db=db, owner_id=current_user.id, skip=skip, limit=limit
    )
    return items


@router.post("/", response_model=schemas.Item)
def create_item(
    item_in: schemas.ItemCreate,
    db: Session = Depends(deps.get_db),
    current_user: schemas.UserInDB = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new item.
    """
    item = crud.item.create_with_owner(db=db, obj_in=item_in, owner_id=current_user.id)
    return item


@router.put("/{id}", response_model=schemas.Item)
def update_item(
    item_in: schemas.ItemUpdate,
    db: Session = Depends(deps.get_db),
    item: models.Item = Depends(deps.get_owned_item_by_id),
    current_user: schemas.UserInDB = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update an item.
    """
    item = crud.item.update(db=db, db_obj=item, obj_in=item_in)
    return item


@router.get("/{id}", response_model=schemas.Item)
def read_item(
    db: Session = Depends(deps.get_db),
    item: models.Item = Depends(deps.get_owned_item_by_id),
    current_user: schemas.UserInDB = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get item by ID.
    """
    return item


@router.delete("/{id}", response_model=schemas.Item)
def delete_item(
    db: Session = Depends(deps.get_db),
    item: models.Item = Depends(deps.get_owned_item_by_id),
    current_user: schemas.UserInDB = Depends(deps.get_current_active_user),
) -> Any:
    """
    Delete an item.
    """
    item = crud.item.remove(db=db, id=item.id)
    return item
