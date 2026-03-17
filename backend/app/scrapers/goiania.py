"""
Scraper do portal de Diários Oficiais da Prefeitura de Goiânia.
URL: https://www.goiania.go.gov.br/shtml//portal/casacivil/lista_diarios.asp?ano=YYYY
"""
import re
import unicodedata
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
    def _normalizar_texto(texto: str) -> str:
        sem_acentos = "".join(
            ch for ch in unicodedata.normalize("NFD", texto)
            if unicodedata.category(ch) != "Mn"
        )
        sem_ordinais = re.sub(r"(\d{1,2})\s*[º°o]\b", r"\1", sem_acentos, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", sem_ordinais).strip().lower()

    @staticmethod
    def _extrair_data_do_texto(texto_link: str) -> date | None:
        meses = {
            "janeiro": 1,
            "fevereiro": 2,
            "marco": 3,
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

        normalizado = GoianiaScraper._normalizar_texto(texto_link)
        m = re.search(r"(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})", normalizado)
        if not m:
            return None

        dia = int(m.group(1))
        mes_nome = m.group(2)
        ano = int(m.group(3))
        mes = meses.get(mes_nome)
        if not mes:
            return None

        try:
            return date(ano, mes, dia)
        except ValueError:
            return None

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

        # Prioridade 1: data do texto apresentado no portal.
        data_texto = GoianiaScraper._extrair_data_do_texto(texto_link) if texto_link else None
        if data_texto:
            data_edicao = data_texto

        # Prioridade 2: data no nome do arquivo (fallback).
        if not data_texto and len(partes) > 1:
            try:
                data_edicao = datetime.strptime(partes[1], "%Y%m%d").date()
            except ValueError:
                pass

        edicao = str(int(partes[2])) if len(partes) > 2 else ""

        tipo = "Normal"
        if len(partes) > 3:
            sufixo = partes[3].lower()
            tipo = {"edi": "Edição Extra", "suplemento": "Suplemento"}.get(sufixo, sufixo.capitalize())

        return edicao, data_edicao, tipo
