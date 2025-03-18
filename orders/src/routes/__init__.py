from fastapi import APIRouter

from src.routes.health import router as health_router
from src.routes.menu import router as menu_router
from src.routes.orders import router as orders_router

router = APIRouter(prefix="/api/v1")
router.include_router(menu_router)
router.include_router(orders_router)
