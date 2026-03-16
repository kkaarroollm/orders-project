from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.lifespan import startup, teardown
from src.routes import router
from src.settings import settings


@asynccontextmanager
async def lifespan(app_: FastAPI) -> AsyncGenerator[None]:
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

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

app.add_middleware(GZipMiddleware)  # ty: ignore[invalid-argument-type]
app.add_middleware(
    CORSMiddleware,  # ty: ignore[invalid-argument-type]
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)
