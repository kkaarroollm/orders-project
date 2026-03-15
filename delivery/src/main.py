from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import settings
from src.lifespan import startup, teardown
from src.routes import router


@asynccontextmanager
async def lifespan(app_: FastAPI) -> AsyncIterator[None]:
    await startup(app_)
    yield
    await teardown(app_)


app = FastAPI(
    title=settings.title,
    version=settings.version,
    contact={"name": settings.contact_name, "email": settings.contact_email},
    lifespan=lifespan,
)

app.include_router(router)
