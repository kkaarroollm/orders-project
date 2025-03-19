from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.lifespan import startup, teardown
from src.routes import health_router, router


@asynccontextmanager
async def lifespan(app_: FastAPI) -> AsyncGenerator:
    """Handles application startup and shutdown."""
    await startup(app_)
    yield
    await teardown(app_)


app = FastAPI(
    title="Orders Service",
    version="1.0.0",
    contact={"name": "kkaarroollm", "email": "mkarol.4514@gmail.com"},  # noqa
    lifespan=lifespan,
)
app.include_router(router)
app.include_router(health_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # TODO: go to env stages
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
