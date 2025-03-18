from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.lifespan import startup, teardown
from src.routes import health_router


@asynccontextmanager
async def lifespan(app_: FastAPI) -> AsyncGenerator:
    """Handles application startup and shutdown."""
    await startup(app_)
    yield
    await teardown(app_)


app = FastAPI(
    title="Notifications Service",
    version="1.0.0",
    contact={"name": "kkaarroollm", "email": "mkarol.4514@gmail.com"},  # noqa
    lifespan=lifespan,
)

app.include_router(health_router)
