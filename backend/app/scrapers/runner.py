"""
Ponto de entrada CLI para executar o scraper manualmente.
Uso: python -m app.scrapers.runner --portal goiania --ano 2025
"""
import argparse
import csv
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from app.core.config import settings
from app.core.exceptions import GovScanException, ProcessorException
from app.processors.pdf_processor import contar_paginas
from app.scrapers.registry import get_scraper, list_portals


def run(portal_id: str, ano: int, output_csv: str) -> None:
    scraper = get_scraper(portal_id)

    print(f"\n[GovScan] Portal: {portal_id} | Ano: {ano}")
    print(f"[GovScan] Extraindo links...")

    diarios = scraper.extrair_links(ano)
    total = len(diarios)
    print(f"[GovScan] {total} PDFs encontrados\n")

    resultados = []
    concluidos = 0

    with ThreadPoolExecutor(max_workers=settings.SCRAPER_MAX_WORKERS) as executor:
        futures = {executor.submit(contar_paginas, d.url): d for d in diarios}

        for future in as_completed(futures):
            concluidos += 1
            diario = futures[future]
            try:
                paginas = future.result()
                status, erro = "ok", ""
            except ProcessorException as e:
                paginas, status, erro = None, "error", str(e)

            resultados.append({
                "portal":       diario.portal,
                "municipio":    diario.municipio,
                "edicao":       diario.edicao,
                "data_edicao":  diario.data_edicao.strftime("%d/%m/%Y"),
                "tipo":         diario.tipo,
                "paginas":      paginas,
                "status":       status,
                "erro":         erro,
                "url":          diario.url,
                "nome_arquivo": diario.nome_arquivo,
            })

            icone = "✓" if status == "ok" else "✗"
            pags = str(paginas) if paginas else "ERRO"
            print(
                f"  [{concluidos:>4}/{total}] {icone} "
                f"Ed. {diario.edicao:<8} | "
                f"{diario.data_edicao} | "
                f"{diario.tipo:<15} | {pags:>5} págs"
                + (f" | {erro[:60]}" if erro else "")
            )

    resultados.sort(key=lambda x: x["edicao"])
    _salvar_csv(resultados, output_csv)
    _imprimir_resumo(resultados)


def _salvar_csv(resultados: list[dict], caminho: str) -> None:
    campos = ["portal", "municipio", "edicao", "data_edicao", "tipo",
              "paginas", "status", "erro", "url", "nome_arquivo"]
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)
    print(f"\n[GovScan] Relatório salvo: {caminho}")


def _imprimir_resumo(resultados: list[dict]) -> None:
    ok = [r for r in resultados if r["status"] == "ok"]
    erros = [r for r in resultados if r["status"] != "ok"]
    total_pags = sum(r["paginas"] for r in ok)

    print("\n" + "═" * 55)
    print("  RESUMO")
    print("═" * 55)
    print(f"  Total processados : {len(resultados)}")
    print(f"  Sucesso           : {len(ok)}")
    print(f"  Erros             : {len(erros)}")
    print(f"  Total de páginas  : {total_pags:,}")
    if ok:
        print(f"  Média págs/edição : {total_pags / len(ok):.1f}")
    print("═" * 55)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GovScan - Extrator de Diários Oficiais")
    parser.add_argument("--portal", required=True, choices=list_portals())
    parser.add_argument("--ano",    required=True, type=int)
    parser.add_argument("--output", default=f"govscan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    args = parser.parse_args()

    try:
        run(args.portal, args.ano, args.output)
    except GovScanException as e:
        print(f"[ERRO] {e}", file=sys.stderr)
        sys.exit(1)
