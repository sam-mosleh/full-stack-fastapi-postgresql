from typing import Any, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.Item])
def read_items(
    skip: int = 0,
    limit: int = 100,
    owner: Optional[schemas.UserInDB] = Depends(deps.get_owner_by_id),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Retrieve items.
    """
    if owner is None:
        items = crud.item.get_multi(db, skip=skip, limit=limit)
    else:
        items = crud.item.get_multi_by_owner(
            db, owner_id=owner.id, skip=skip, limit=limit
        )
    return items


@router.put("/{id}", response_model=schemas.Item)
def update_item(
    item_in: schemas.ItemUpdate,
    db: Session = Depends(deps.get_db),
    item: models.Item = Depends(deps.get_item_by_id),
) -> Any:
    """
    Update an item.
    """
    item = crud.item.update(db=db, db_obj=item, obj_in=item_in)
    return item


@router.get("/{id}", response_model=schemas.Item)
def read_item(item: models.Item = Depends(deps.get_item_by_id)) -> Any:
    """
    Get item by ID.
    """
    return item


@router.delete("/{id}", response_model=schemas.Item)
def delete_item(
    db: Session = Depends(deps.get_db), item: models.Item = Depends(deps.get_item_by_id)
) -> Any:
    """
    Delete an item.
    """
    item = crud.item.remove(db=db, id=item.id)
    return item
