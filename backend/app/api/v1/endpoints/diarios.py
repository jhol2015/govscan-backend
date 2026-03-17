from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.diario import DiarioListResponse, SincronizacaoProgressoResponse
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


@router.get(
    "/sincronizar/progresso",
    response_model=SincronizacaoProgressoResponse,
    summary="Retorna o progresso da sincronização do portal/ano",
)
async def progresso_sincronizacao(
    portal: str = Query(..., description="ID do portal, ex: goiania"),
    ano: int = Query(..., description="Ano processado, ex: 2025"),
):
    snapshot = DiarioService.obter_progresso(portal_id=portal, ano=ano)
    if snapshot:
        return snapshot
    return {
        "portal": portal,
        "ano": ano,
        "total": 0,
        "processados": 0,
        "ok": 0,
        "erros": 0,
        "pendentes": 0,
        "progresso": 0,
        "status": "idle",
        "mensagem": "Sem sincronização ativa para este portal/ano",
    }


@router.post("/limpar", summary="Remove todos os diários para iniciar extração do zero")
async def limpar_diarios(
    db: AsyncSession = Depends(get_db),
):
    service = DiarioService(db)
    return await service.limpar_todos()


@router.get("/validar-extracao", summary="Compara links esperados no portal com os registros extraídos")
async def validar_extracao(
    portal: str = Query(..., description="ID do portal, ex: goiania"),
    ano: int = Query(..., description="Ano processado, ex: 2025"),
    db: AsyncSession = Depends(get_db),
):
    service = DiarioService(db)
    return await service.validar_extracao(portal_id=portal, ano=ano)
