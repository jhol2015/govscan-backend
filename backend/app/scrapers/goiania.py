"""
Scraper do portal de Diários Oficiais da Prefeitura de Goiânia.
URL: https://www.goiania.go.gov.br/shtml//portal/casacivil/lista_diarios.asp?ano=YYYY
"""
import re
from datetime import datetime, date

import requests
from bs4 import BeautifulSoup

from app.core.config import settings
from app.core.exceptions import ScraperException
from app.scrapers.base import BaseScraper, DiarioRaw


_BASE_URL = (
    "https://www.goiania.go.gov.br"
    "/shtml//portal/casacivil/lista_diarios.asp"
)
_HEADERS = {"User-Agent": settings.SCRAPER_USER_AGENT}


class GoianiaScraper(BaseScraper):
    """Extrai links de PDF da listagem de Diários Oficiais de Goiânia."""

    @property
    def portal_id(self) -> str:
        return "goiania"

    def extrair_links(self, ano: int) -> list[DiarioRaw]:
        url = f"{_BASE_URL}?ano={ano}"
        try:
            response = requests.get(url, headers=_HEADERS, timeout=settings.SCRAPER_TIMEOUT)
            response.encoding = "windows-1252"
            response.raise_for_status()
        except requests.RequestException as e:
            raise ScraperException(f"Falha ao acessar portal Goiânia ({ano}): {e}") from e

        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a", href=re.compile(r"\.pdf$", re.IGNORECASE))

        diarios: list[DiarioRaw] = []
        for link in links:
            href = link.get("href", "")
            pdf_url = href if href.startswith("http") else f"https://www.goiania.go.gov.br{href}"
            nome_arquivo = pdf_url.split("/")[-1]
            texto_link = link.get_text(" ", strip=True)
            edicao, data_edicao, tipo = self._parsear_nome(nome_arquivo, texto_link)

            diarios.append(DiarioRaw(
                portal=self.portal_id,
                municipio="Goiânia",
                edicao=edicao,
                data_edicao=data_edicao,
                tipo=tipo,
                url=pdf_url,
                nome_arquivo=nome_arquivo,
            ))

        return diarios

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _parsear_nome(nome: str, texto_link: str = "") -> tuple[str, date, str]:
        """
        Extrai edição, data e tipo do nome do arquivo.
        Padrão: do_YYYYMMDD_000008691.pdf
                do_YYYYMMDD_000008691_edi.pdf
                do_YYYYMMDD_000008470_suplemento.pdf
        """
        base = nome.replace(".pdf", "")
        partes = base.split("_")

        data_edicao: date = datetime.today().date()
        data_no_nome_valida = False

        # Prioridade 1: data no nome do arquivo (do_YYYYMMDD_...)
        if len(partes) > 1:
            try:
                data_edicao = datetime.strptime(partes[1], "%Y%m%d").date()
                data_no_nome_valida = True
            except ValueError:
                pass

        # Prioridade 2: data no texto do link (somente se a do nome não existir/for inválida)
        if not data_no_nome_valida and texto_link:
            meses = {
                "janeiro": 1,
                "fevereiro": 2,
                "marco": 3,
                "março": 3,
                "abril": 4,
                "maio": 5,
                "junho": 6,
                "julho": 7,
                "agosto": 8,
                "setembro": 9,
                "outubro": 10,
                "novembro": 11,
                "dezembro": 12,
            }
            m = re.search(
                r"(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})",
                texto_link.lower(),
                flags=re.IGNORECASE,
            )
            if m:
                dia = int(m.group(1))
                mes_nome = m.group(2)
                ano = int(m.group(3))
                mes = meses.get(mes_nome)
                if mes:
                    try:
                        data_edicao = date(ano, mes, dia)
                    except ValueError:
                        pass

        edicao = str(int(partes[2])) if len(partes) > 2 else ""

        tipo = "Normal"
        if len(partes) > 3:
            sufixo = partes[3].lower()
            tipo = {"edi": "Edição Extra", "suplemento": "Suplemento"}.get(sufixo, sufixo.capitalize())

        return edicao, data_edicao, tipo
