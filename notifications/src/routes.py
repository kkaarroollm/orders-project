from fastapi import APIRouter, Request, Response, status

router = APIRouter(prefix="/api/v1")


@router.get("/health/liveness")
async def liveness() -> Response:
    return Response(content='{"status":"ok"}', media_type="application/json")


@router.get("/health/readiness")
async def readiness(request: Request) -> Response:
    ctx = getattr(request.app.state, "ctx", None)
    # A live HTTP server with dead stream consumers is not ready: it would keep
    # taking traffic while no events are processed.
    if not ctx or not ctx.ready or (ctx.event_bus and not ctx.event_bus.healthy):
        return Response(
            content='{"status":"not ready"}',
            media_type="application/json",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return Response(content='{"status":"ok"}', media_type="application/json")
