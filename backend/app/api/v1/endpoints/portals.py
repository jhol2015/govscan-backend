from fastapi import APIRouter
from app.scrapers.registry import list_portals

router = APIRouter(prefix="/portals", tags=["Portais"])


@router.get("/", summary="Lista portais disponíveis")
async def listar_portais():
    return {"portais": list_portals()}
