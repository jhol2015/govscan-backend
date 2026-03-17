"""
Orquestra scraper + processor + repository.
A API chama o service; o service não conhece HTTP.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ProcessorException
from app.processors.pdf_processor import contar_paginas
from app.repositories.diario_repository import DiarioRepository
from app.scrapers.registry import get_scraper
from app.schemas.diario import DiarioCreate, DiarioListResponse, DiarioUpdate


_sync_progress: dict[str, dict] = {}
_sync_progress_lock = Lock()


def _sync_key(portal_id: str, ano: int) -> str:
    return f"{portal_id}:{ano}"


class DiarioService:
    def __init__(self, db: AsyncSession):
        self.repo = DiarioRepository(db)

    @staticmethod
    def obter_progresso(portal_id: str, ano: int) -> dict | None:
        key = _sync_key(portal_id, ano)
        with _sync_progress_lock:
            snapshot = _sync_progress.get(key)
            return dict(snapshot) if snapshot else None

    @staticmethod
    def _atualizar_progresso(portal_id: str, ano: int, **values) -> dict:
        key = _sync_key(portal_id, ano)
        with _sync_progress_lock:
            current = _sync_progress.get(key, {
                "portal": portal_id,
                "ano": ano,
                "total": 0,
                "processados": 0,
                "ok": 0,
                "erros": 0,
                "pendentes": 0,
                "progresso": 0,
                "status": "idle",
                "mensagem": None,
            })
            current.update(values)
            total = max(0, int(current.get("total", 0)))
            processados = max(0, int(current.get("processados", 0)))
            current["pendentes"] = max(0, total - processados)
            current["progresso"] = round((processados / total) * 100) if total > 0 else 0
            _sync_progress[key] = current
            return dict(current)

    async def sincronizar(self, portal_id: str, ano: int) -> dict:
        """Extrai links, conta páginas e persiste no banco."""
        scraper = get_scraper(portal_id)
        diarios_raw = scraper.extrair_links(ano)
        total = len(diarios_raw)

        self._atualizar_progresso(
            portal_id,
            ano,
            total=total,
            processados=0,
            ok=0,
            erros=0,
            status="running",
            mensagem="Sincronização iniciada",
        )

        salvos, erros = 0, 0
        processados = 0

        try:
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

                    processados += 1
                    if status == "ok":
                        salvos += 1
                    else:
                        erros += 1

                    self._atualizar_progresso(
                        portal_id,
                        ano,
                        processados=processados,
                        ok=salvos,
                        erros=erros,
                        status="running",
                        mensagem="Sincronização em andamento",
                    )

            self._atualizar_progresso(
                portal_id,
                ano,
                processados=processados,
                ok=salvos,
                erros=erros,
                status="completed",
                mensagem="Sincronização concluída",
            )
            return {"portal": portal_id, "ano": ano, "salvos": salvos, "erros": erros}
        except Exception as exc:
            self._atualizar_progresso(
                portal_id,
                ano,
                status="failed",
                mensagem=str(exc),
            )
            raise

    async def listar(
        self, portal: str | None, skip: int, limit: int
    ) -> DiarioListResponse:
        total, items = await self.repo.list(portal=portal, skip=skip, limit=limit)
        return DiarioListResponse(total=total, items=items)

    async def limpar_todos(self) -> dict:
        total, _ = await self.repo.list(portal=None, skip=0, limit=1)
        await self.repo.clear_all()
        self._atualizar_progresso(
            portal_id="*",
            ano=0,
            total=0,
            processados=0,
            ok=0,
            erros=0,
            status="idle",
            mensagem="Base limpa para nova extração",
        )
        return {"removidos": total, "restantes": 0}

    async def validar_extracao(self, portal_id: str, ano: int) -> dict:
        scraper = get_scraper(portal_id)
        diarios_raw = scraper.extrair_links(ano)
        esperados = {d.url for d in diarios_raw}

        encontrados_urls: set[str] = set()
        ok = 0
        erro = 0
        skip = 0
        limit = 500
        total = 1

        while skip < total:
            total, items = await self.repo.list(portal=portal_id, skip=skip, limit=limit)
            for item in items:
                if item.data_edicao.year != ano:
                    continue
                encontrados_urls.add(item.url)
                if item.status == "ok":
                    ok += 1
                elif item.status == "error":
                    erro += 1
            skip += limit
            if not items:
                break

        faltantes = sorted(esperados - encontrados_urls)
        extras = sorted(encontrados_urls - esperados)

        return {
            "portal": portal_id,
            "ano": ano,
            "esperados": len(esperados),
            "encontrados": len(encontrados_urls),
            "ok": ok,
            "erros": erro,
            "faltantes": len(faltantes),
            "extras": len(extras),
            "faltantes_amostra": faltantes[:20],
            "extras_amostra": extras[:20],
            "status": "completo" if len(faltantes) == 0 else "incompleto",
        }
