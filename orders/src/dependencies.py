from fastapi import Request

from src.services.menu_service import MenuService
from src.services.order_service import OrderService
from src.state import AppState


def get_app_state(request: Request) -> AppState:
    return request.app.state.ctx


def get_menu_service(request: Request) -> MenuService:
    return get_app_state(request).menu_service


def get_order_service(request: Request) -> OrderService:
    return get_app_state(request).order_service
