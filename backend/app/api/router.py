from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.requests import router as requests_router
from app.api.routes.equipment import router as equipment_router
from app.api.routes.teams import router as teams_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(requests_router, tags=["requests"])
api_router.include_router(equipment_router, tags=["equipment"])
api_router.include_router(teams_router, tags=["teams"])
