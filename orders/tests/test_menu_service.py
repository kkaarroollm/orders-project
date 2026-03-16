from unittest.mock import AsyncMock, MagicMock

import pytest

from src.schemas import MenuItemSchema
from src.services.menu_service import MenuService


@pytest.fixture
def menu_repo():
    return AsyncMock()


@pytest.fixture
def mongo_client():
    client = MagicMock()
    session = AsyncMock()
    client.start_session.return_value = session
    session.start_transaction = AsyncMock()
    session.commit_transaction = AsyncMock()
    session.end_session = AsyncMock()
    return client


@pytest.fixture
def service(menu_repo, mongo_client):
    return MenuService(repo=menu_repo, mongo_client=mongo_client)


def _make_item(**overrides):
    defaults = {"name": "Burger", "price": 9.99, "category": "food", "stock": 10}
    defaults.update(overrides)
    return MenuItemSchema(**defaults)


@pytest.mark.asyncio
async def test_get_item(service, menu_repo):
    item = _make_item()
    menu_repo.get_by_id.return_value = item

    result = await service.get_item("item123")

    assert result == item
    menu_repo.get_by_id.assert_called_once_with("item123", session=None)


@pytest.mark.asyncio
async def test_get_item_not_found(service, menu_repo):
    menu_repo.get_by_id.return_value = None

    result = await service.get_item("missing")

    assert result is None


@pytest.mark.asyncio
async def test_list_items(service, menu_repo):
    items = [_make_item(name="Burger"), _make_item(name="Pizza")]
    menu_repo.find_many.return_value = items

    result = await service.list_items()

    assert len(result) == 2
    menu_repo.find_many.assert_called_once_with({}, session=None)


@pytest.mark.asyncio
async def test_create_item(service, menu_repo):
    menu_repo.create.return_value = "newid"
    item = _make_item()

    result = await service.create_item(item)

    assert result == "newid"
