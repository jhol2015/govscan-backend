from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.diario import DiarioListResponse
from app.services.diario_service import DiarioService

router = APIRouter(prefix="/diarios", tags=["Diários"])


@router.get("/", response_model=DiarioListResponse)
async def listar_diarios(
    portal: str | None = Query(None, description="Filtrar por portal, ex: goiania"),
    skip:   int        = Query(0,    ge=0),
    limit:  int        = Query(100,  le=500),
    db: AsyncSession   = Depends(get_db),
):
    service = DiarioService(db)
    return await service.listar(portal=portal, skip=skip, limit=limit)


@router.post("/sincronizar", summary="Extrai e persiste diários de um portal/ano")
async def sincronizar(
    portal: str        = Query(..., description="ID do portal, ex: goiania"),
    ano:    int        = Query(..., description="Ano a processar, ex: 2025"),
    db: AsyncSession   = Depends(get_db),
):
    service = DiarioService(db)
    return await service.sincronizar(portal_id=portal, ano=ano)
