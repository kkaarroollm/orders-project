from fastapi import APIRouter, Request, Response, status

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/liveness")
async def liveness() -> Response:
    return Response(content='{"status":"ok"}', media_type="application/json")


@router.get("/readiness")
async def readiness(request: Request) -> Response:
    if not getattr(request.app.state, "ready", False):
        return Response(
            content='{"status":"not ready"}',
            media_type="application/json",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return Response(content='{"status":"ok"}', media_type="application/json")
