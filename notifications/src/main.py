from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from prometheus_client import make_asgi_app
from shared.http_metrics import GZipMiddleware, PrometheusMiddleware
from shared.tracing import instrument_app

from src.lifespan import startup, teardown
from src.routes import router
from src.settings import settings
from src.sse import event_stream, order_stream_registry
from src.state import AppState


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


@app.get("/api/v1/order-tracking/{order_id}")
async def order_tracking(order_id: str) -> StreamingResponse:
    """Server-sent events for one order.

    Order tracking is one-way, so this needs no upgrade handshake: it is
    covered by CORSMiddleware, reconnects natively, and needs no application
    heartbeat.
    """
    state: AppState = app.state.ctx
    snapshot = await state.notification_repository.get_order_status(order_id)

    return StreamingResponse(
        event_stream(order_stream_registry, order_id, snapshot),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            # Stops nginx buffering the stream into silence.
            "X-Accel-Buffering": "no",
        },
    )


app.include_router(router)

app.mount("/metrics", make_asgi_app())

instrument_app(app)

app.add_middleware(PrometheusMiddleware)  # ty: ignore[invalid-argument-type]
app.add_middleware(GZipMiddleware)  # ty: ignore[invalid-argument-type]
app.add_middleware(
    CORSMiddleware,  # ty: ignore[invalid-argument-type]
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)
