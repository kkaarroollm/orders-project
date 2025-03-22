from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.lifespan import startup, teardown
from src.routes import health_router, router


@asynccontextmanager
async def lifespan(app_: FastAPI) -> AsyncGenerator:
    """Handles application startup and shutdown."""
    await startup(app_)
    yield
    await teardown(app_)


app = FastAPI(
    title=settings.title,
    version=settings.version,
    contact={"name": settings.contact_name, "email": settings.contact_email},  # noqa
    lifespan=lifespan,
)
app.include_router(router)
app.include_router(health_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
