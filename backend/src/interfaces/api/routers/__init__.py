"""Routers package — exposes all APIRouter instances."""

from backend.src.interfaces.api.routers.articles import router as articles_router
from backend.src.interfaces.api.routers.profile import router as profile_router
from backend.src.interfaces.api.routers.sources import router as sources_router

__all__ = ["articles_router", "profile_router", "sources_router"]
