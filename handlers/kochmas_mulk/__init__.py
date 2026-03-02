"""Ko'chmas Mulk Handler'lari"""
from .sell import router as sell_router
from .buy import router as buy_router
from .main import router as main_router
from .my_objects import router as my_objects_router

__all__ = ['sell_router', 'buy_router', 'main_router', 'my_objects_router']