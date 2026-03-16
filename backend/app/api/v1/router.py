from fastapi import APIRouter
from app.api.v1.endpoints import diarios, portals

router = APIRouter(prefix="/api/v1")
router.include_router(diarios.router)
router.include_router(portals.router)
