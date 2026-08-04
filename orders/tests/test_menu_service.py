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
def menu_cache():
    cache = AsyncMock()
    cache.get.return_value = None  # cold cache by default
    return cache


@pytest.fixture
def service(menu_repo, menu_cache, mongo_client):
    return MenuService(
        repo=menu_repo,
        read_repo=menu_repo,
        cache=menu_cache,
        mongo_client=mongo_client,
    )


def _make_item(**overrides):
    return MenuItemSchema(
        name=overrides.get("name", "Burger"),
        price=overrides.get("price", 9.99),
        category=overrides.get("category", "food"),
        stock=overrides.get("stock", 10),
    )


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


@pytest.mark.asyncio
async def test_list_items_caches_a_cold_read(service, menu_repo, menu_cache):
    menu_repo.find_many.return_value = [_make_item()]

    items = await service.list_items()

    assert len(items) == 1
    menu_cache.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_items_serves_the_cache_without_touching_mongo(service, menu_repo, menu_cache):
    menu_cache.get.return_value = [_make_item(name="Cached")]

    items = await service.list_items()

    assert items[0].name == "Cached"
    menu_repo.find_many.assert_not_called()


@pytest.mark.asyncio
async def test_empty_menu_is_still_a_cache_hit(service, menu_repo, menu_cache):
    """An empty list is a real cached value, not a miss."""
    menu_cache.get.return_value = []

    assert await service.list_items() == []
    menu_repo.find_many.assert_not_called()


@pytest.mark.asyncio
async def test_creating_an_item_invalidates_the_cache(service, menu_repo, menu_cache):
    menu_repo.create.return_value = "item123"

    await service.create_item(_make_item())

    menu_cache.invalidate.assert_awaited_once()
