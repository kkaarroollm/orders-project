from fastapi import Request

from src.services.menu_service import MenuService
from src.services.order_service import OrderService


def get_menu_service(request: Request) -> MenuService:
    return request.app.state.menu_service  # type: ignore


def get_order_service(request: Request) -> OrderService:
    return request.app.state.order_service  # type: ignore
