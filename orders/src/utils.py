from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar, Union

from motor.motor_asyncio import AsyncIOMotorClient

T = TypeVar("T")

ClientOrCallable = Union[AsyncIOMotorClient, Callable[..., AsyncIOMotorClient]]


def with_mongodb_transaction(
    client_or_callable: ClientOrCallable,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator for wrapping a function with a MongoDB transaction,
    using the provided client or callable to get the client."""

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            if callable(client_or_callable):
                db_client = client_or_callable(*args, **kwargs)
            else:
                db_client = client_or_callable

            async with await db_client.start_session() as session:
                async with session.start_transaction():
                    try:
                        return await func(*args, session=session, **kwargs)
                    except Exception as e:
                        await session.abort_transaction()
                        raise e

        return wrapper

    return decorator
