from fastapi import APIRouter
from src.routes.health import router as health_router
from src.routes.order_tracking import router as order_tracking_router

router = APIRouter(prefix="/api/v1")
router.include_router(order_tracking_router)
