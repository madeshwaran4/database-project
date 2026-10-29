from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.enrollment import router as enrollment_router
from app.api.voting import router as voting_router
from app.api.admin import router as admin_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(enrollment_router)
api_router.include_router(voting_router)
api_router.include_router(admin_router)

__all__ = ["api_router"]
