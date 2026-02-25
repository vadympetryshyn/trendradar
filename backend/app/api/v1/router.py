from fastapi import APIRouter

from app.api.v1.niches import router as niches_router
from app.api.v1.trends import router as trends_router
from app.api.v1.admin import router as admin_router
from app.api.v1.external_trends import router as external_trends_router
from app.api.v1.external_niches import router as external_niches_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(niches_router)
api_v1_router.include_router(trends_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(external_trends_router)
api_v1_router.include_router(external_niches_router)
