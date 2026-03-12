from fastapi import APIRouter
from .health import router as health_router
from .auth import router as auth_router
from .documents import router as documents_router
from .analysis import router as analysis_router
from .reports import router as reports_router
from .schemas import router as schemas_router

api_router = APIRouter()
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
api_router.include_router(schemas_router, prefix="/schemas", tags=["schemas"])
