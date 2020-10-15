from typing import Dict

import pytest
from fastapi.testclient import TestClient
from requests.exceptions import HTTPError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.item import Item
from app.models.user import User
from app.tests.utils.item import create_random_item


def test_create_item(
    client: TestClient,
    normal_user_token_headers: Dict[str, str],
    normal_user: User,
    db: Session,
) -> None:
    data = {"title": "Foo", "description": "Fighters"}
    response = client.post(
        f"{settings.API_V1_STR}/items/", headers=normal_user_token_headers, json=data,
    )
    response.raise_for_status()
    content = response.json()
    assert "id" in content
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert content["owner_id"] == str(normal_user.id)


def test_read_specific_item_by_superuser(
    client: TestClient, superuser_token_headers: Dict[str, str], new_item: Item
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/admin/items/{new_item.id}",
        headers=superuser_token_headers,
    )
    response.raise_for_status()
    content = response.json()
    assert content["title"] == new_item.title
    assert content["description"] == new_item.description
    assert content["id"] == new_item.id
    assert content["owner_id"] == str(new_item.owner_id)


def test_read_all_items_of_specific_user_by_superuser(
    client: TestClient,
    superuser_token_headers: Dict[str, str],
    new_user: User,
    new_item: Item,
    db: Session,
) -> None:
    second_item = create_random_item(db, owner_id=new_user.id)
    response = client.get(
        f"{settings.API_V1_STR}/admin/items/",
        headers=superuser_token_headers,
        params={"owner_id": new_user.id},
    )
    response.raise_for_status()
    all_items = response.json()
    assert len(all_items) == 2
    assert all_items[0]["owner_id"] == str(new_user.id)
    assert all_items[1]["owner_id"] == str(new_user.id)


def test_read_specific_item_by_owner(
    client: TestClient,
    normal_user_token_headers: Dict[str, str],
    normal_user: User,
    db: Session,
) -> None:
    new_item = create_random_item(db, owner_id=normal_user.id)
    response = client.get(
        f"{settings.API_V1_STR}/items/{new_item.id}", headers=normal_user_token_headers,
    )
    response.raise_for_status()
    content = response.json()
    assert content["title"] == new_item.title
    assert content["description"] == new_item.description
    assert content["id"] == new_item.id
    assert content["owner_id"] == str(new_item.owner_id)


def test_read_specific_item_by_non_owner(
    client: TestClient, normal_user_token_headers: Dict[str, str], new_item: Item
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items/{new_item.id}", headers=normal_user_token_headers,
    )
    with pytest.raises(HTTPError):
        response.raise_for_status()
    content = response.json()
    assert "id" not in content


def test_retrieve_items_by_owner(
    client: TestClient, normal_user_token_headers: Dict[str, str], normal_user: User
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items", headers=normal_user_token_headers,
    )
    response.raise_for_status()
    all_items = response.json()
    for item in all_items:
        assert "id" in item
        assert item["owner_id"] == str(normal_user.id)
