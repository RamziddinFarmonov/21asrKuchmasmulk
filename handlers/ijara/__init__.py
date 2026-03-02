"""Ijara Handler'lari"""
from .main import router as main_router
from .my_objects import router as my_objects_router

__all__ = ['main_router', 'my_objects_router']