import logging
from decimal import Decimal

from pymongo import AsyncMongoClient
from pymongo.errors import DuplicateKeyError
from shared.db.idempotency import IdempotencyStore
from shared.db.outbox import MongoOutbox
from shared.events.order import (
    OrderCreated,
    OrderSimulationRequested,
    OrderStatusChanged,
    OrderStatusSimulated,
)

from src.cache import MenuCache
from src.repositories.menu_item_repo import MenuItemRepository
from src.repositories.order_repository import OrderRepository
from src.responses import OrderResponse
from src.schemas import OrderSchema, OrderStatus
from src.services.mixins import TransactionServiceMixin


class OrderRejectedError(Exception):
    """Raised inside an order transaction so it aborts instead of committing.

    Returning from inside `async with self.transaction()` is a *normal* context
    exit, which commits -- leaving the stock already decremented for earlier
    items while no order was created.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class RequestInProgressError(Exception):
    """An idempotency key is reserved but its response is not stored yet.

    Either another request is mid-flight, or one crashed between committing and
    recording its response. Replaying is unsafe, so the caller retries later.
    """


class OrderService(TransactionServiceMixin):
    def __init__(  # noqa: PLR0913 — collaborators are injected, not configured
        self,
        order_repo: OrderRepository,
        order_read_repo: OrderRepository,
        menu_repo: MenuItemRepository,
        outbox: MongoOutbox,
        idempotency: IdempotencyStore,
        menu_cache: MenuCache,
        mongo_client: AsyncMongoClient,
    ) -> None:
        super().__init__(mongo_client)
        self._order_repo = order_repo
        # Reads may go to a secondary; writes and transactions must not.
        self._order_read_repo = order_read_repo
        self._menu_repo = menu_repo
        self._outbox = outbox
        self._idempotency = idempotency
        self._menu_cache = menu_cache

    async def get(self, order_id: str) -> OrderSchema | None:
        return await self._order_read_repo.get_by_id(order_id, session=None)

    async def create_order_with_stock_check(
        self, order_data: OrderSchema, idempotency_key: str | None = None
    ) -> OrderResponse:
        if idempotency_key and (replay := await self._replay(idempotency_key)):
            return replay

        try:
            async with self.transaction() as session:
                if idempotency_key:
                    # Reserved inside the transaction, so the key is only taken
                    # if the order it stands for is actually created.
                    await self._idempotency.reserve(idempotency_key, session)

                total_price = Decimal("0.00")

                for item in order_data.items:
                    menu_item = await self._menu_repo.get_by_id(item.item_id, session=None)
                    if not menu_item:
                        raise OrderRejectedError(f"Item with id={item.item_id} not found")

                    success = await self._menu_repo.decrement_stock(item.item_id, item.quantity, session)
                    if not success:
                        raise OrderRejectedError(f"Not enough stock for item_id={item.item_id}")

                    total_price += Decimal(str(menu_item.price)) * item.quantity

                order_data.total_price = total_price
                order_id_str = await self._order_repo.create(order_data, session)
                order_data.id = order_id_str

                # Staged in the same transaction as the order: the relay
                # publishes them once, and only if, this commits.
                await self._outbox.add(
                    OrderCreated(
                        id=order_id_str,
                        status=order_data.status.value,
                        simulation=order_data.simulation,
                    ),
                    session,
                    correlation_id=order_id_str,
                )

                if order_data.simulation != -1:
                    await self._outbox.add(
                        OrderSimulationRequested(id=order_id_str),
                        session,
                        correlation_id=order_id_str,
                    )
        except OrderRejectedError as rejected:
            logging.info("Rejected order: %s", rejected.message)
            return OrderResponse(order=order_data, success=False, message=rejected.message)
        except DuplicateKeyError:
            # A concurrent request won the key; return whatever it produced.
            if idempotency_key and (replay := await self._replay(idempotency_key)):
                return replay
            raise RequestInProgressError from None

        # Stock just moved, so the cached menu is stale.
        await self._menu_cache.invalidate()

        response = OrderResponse(order=order_data, success=True)
        if idempotency_key:
            await self._idempotency.complete(idempotency_key, response.model_dump(mode="json"))
        return response

    async def _replay(self, idempotency_key: str) -> OrderResponse | None:
        record = await self._idempotency.find(idempotency_key)
        if record is None:
            return None
        if record.get("response") is None:
            raise RequestInProgressError
        logging.info("Replaying stored response for idempotency key %s", idempotency_key)
        return OrderResponse.model_validate(record["response"])

    async def update_order_status(self, order_id: str, new_status: OrderStatus) -> OrderResponse:
        async with self.transaction() as session:
            order = await self._order_repo.advance_status(order_id, new_status, session)
            if order:
                await self._outbox.add(
                    # The order's own simulation flag, not a default: consumers
                    # decide whether to simulate from what the client asked for.
                    OrderStatusChanged(
                        id=order_id,
                        status=new_status.value,
                        simulation=order.simulation,
                    ),
                    session,
                    correlation_id=order_id,
                )

        if order:
            return OrderResponse(order=None, success=True, message=f"Order {order_id} updated to {new_status}")

        return OrderResponse(order=None, success=False, message="Order not found or transition not allowed")

    async def handle_status_update(self, event: OrderStatusSimulated) -> None:
        status = OrderStatus(event.status)
        result = await self.update_order_status(event.id, status)
        if not result.success:
            # Stale or replayed transition: nothing to do, and not a failure.
            logging.info("Ignored %s for order %s: %s", status, event.id, result.message)
