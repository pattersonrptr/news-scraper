"""Routers package — exposes all APIRouter instances."""

from backend.src.interfaces.api.routers.alerts import router as alerts_router
from backend.src.interfaces.api.routers.articles import router as articles_router
from backend.src.interfaces.api.routers.auth import router as auth_router
from backend.src.interfaces.api.routers.profile import router as profile_router
from backend.src.interfaces.api.routers.sources import router as sources_router

__all__ = [
    "alerts_router",
    "articles_router",
    "auth_router",
    "profile_router",
    "sources_router",
]
