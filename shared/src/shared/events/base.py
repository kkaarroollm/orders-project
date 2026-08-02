from datetime import UTC, datetime
from typing import ClassVar
from uuid import uuid4

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base for every event published on a stream.

    `stream` and `event_type` are class-level, so a call site names the event
    class and never a stream string. `event_id` gives consumers a stable key to
    deduplicate on.
    """

    stream: ClassVar[str]
    event_type: ClassVar[str]
    # Wire values this class also answers to, so a rename can roll out without
    # dropping messages already sitting in a stream.
    legacy_types: ClassVar[tuple[str, ...]] = ()

    event_id: str = Field(default_factory=lambda: uuid4().hex)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class OrderEvent(DomainEvent):
    """An event about an order, keyed by the order's own id."""

    id: str
    status: str
    # Present on `order.created`; defaulted on status changes, which do not
    # carry it. Preserves existing behaviour -- see PR 7 (state machine).
    simulation: int = 1

    @property
    def order_id(self) -> str:
        return self.id


class DeliveryEvent(DomainEvent):
    """An event about a delivery, keyed by the order it belongs to."""

    order_id: str
    status: str


class SimulationRequest(DomainEvent):
    """Asks the simulator to drive an entity through its status transitions."""

    id: str
