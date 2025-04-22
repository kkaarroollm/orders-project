from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.config import settings
from src.lifespan import startup, teardown
from src.routes import router


@asynccontextmanager
async def lifespan(app_: FastAPI) -> AsyncGenerator:
    """Handles application startup and shutdown."""
    await startup(app_)
    yield
    await teardown(app_)


app: FastAPI = FastAPI(
    title=settings.title,
    version=settings.version,
    contact={
        "name": settings.contact_name,
        "email": settings.contact_email,
    },
    openapi_url=None if not settings.environment.docs_available() else "/openapi.json",
    lifespan=lifespan,
)

app.include_router(router)


app.add_middleware(GZipMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)
