"""
Orquestra scraper + processor + repository.
A API chama o service; o service não conhece HTTP.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ProcessorException
from app.processors.pdf_processor import contar_paginas
from app.repositories.diario_repository import DiarioRepository
from app.scrapers.registry import get_scraper
from app.schemas.diario import DiarioCreate, DiarioListResponse, DiarioUpdate


class DiarioService:
    def __init__(self, db: AsyncSession):
        self.repo = DiarioRepository(db)

    async def sincronizar(self, portal_id: str, ano: int) -> dict:
        """Extrai links, conta páginas e persiste no banco."""
        scraper = get_scraper(portal_id)
        diarios_raw = scraper.extrair_links(ano)

        salvos, erros = 0, 0

        with ThreadPoolExecutor(max_workers=settings.SCRAPER_MAX_WORKERS) as executor:
            futures = {executor.submit(contar_paginas, d.url): d for d in diarios_raw}

            for future in as_completed(futures):
                raw = futures[future]
                try:
                    paginas = future.result()
                    status, erro = "ok", None
                except ProcessorException as e:
                    paginas, status, erro = None, "error", str(e)

                schema = DiarioCreate(
                    portal=raw.portal,
                    municipio=raw.municipio,
                    edicao=raw.edicao,
                    data_edicao=raw.data_edicao,
                    tipo=raw.tipo,
                    url=raw.url,
                    nome_arquivo=raw.nome_arquivo,
                )
                diario = await self.repo.upsert(schema)
                await self.repo.update(diario.id, DiarioUpdate(
                    paginas=paginas, status=status, erro=erro
                ))

                if status == "ok":
                    salvos += 1
                else:
                    erros += 1

        return {"portal": portal_id, "ano": ano, "salvos": salvos, "erros": erros}

    async def listar(
        self, portal: str | None, skip: int, limit: int
    ) -> DiarioListResponse:
        total, items = await self.repo.list(portal=portal, skip=skip, limit=limit)
        return DiarioListResponse(total=total, items=items)
