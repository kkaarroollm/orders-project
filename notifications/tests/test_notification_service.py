from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.service import NotificationService


@pytest.fixture
def notification_repo():
    return AsyncMock()


@pytest.fixture
def ws_manager():
    return AsyncMock()


@pytest.fixture
def service(notification_repo, ws_manager):
    return NotificationService(repo=notification_repo, ws_manager=ws_manager)


@pytest.mark.asyncio
async def test_handle_event_broadcasts_and_caches(service, notification_repo, ws_manager):
    msg = SimpleNamespace(order_id="order123", id=None, status="preparing")

    await service.handle_event(msg)

    ws_manager.broadcast.assert_called_once()
    call_args = ws_manager.broadcast.call_args
    assert call_args[0][0] == "order123"
    assert call_args[0][1]["status"] == "preparing"

    notification_repo.set_order_status.assert_called_once()


@pytest.mark.asyncio
async def test_handle_event_uses_id_as_fallback(service, ws_manager, notification_repo):
    msg = SimpleNamespace(order_id=None, id="order456", status="confirmed")

    await service.handle_event(msg)

    ws_manager.broadcast.assert_called_once()
    call_args = ws_manager.broadcast.call_args
    assert call_args[0][0] == "order456"


@pytest.mark.asyncio
async def test_handle_event_missing_data_raises(service):
    msg = SimpleNamespace(order_id=None, id=None, status=None)

    with pytest.raises(ValueError, match="Invalid data"):
        await service.handle_event(msg)
