"""
Responsabilidade única: baixar um PDF e retornar a contagem de páginas.
Não conhece banco, não conhece scraper — só bytes e pypdf.
"""
import io
import requests
from pypdf import PdfReader
from app.core.config import settings
from app.core.exceptions import ProcessorException


_HEADERS = {"User-Agent": settings.SCRAPER_USER_AGENT}


def contar_paginas(url: str) -> int:
    """
    Faz o download do PDF em memória e retorna o número de páginas.
    Lança ProcessorException em caso de falha.
    """
    try:
        response = requests.get(
            url,
            headers=_HEADERS,
            timeout=settings.SCRAPER_TIMEOUT,
            stream=True,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise ProcessorException(f"HTTP {e.response.status_code} ao baixar {url}") from e
    except requests.exceptions.Timeout:
        raise ProcessorException(f"Timeout após {settings.SCRAPER_TIMEOUT}s: {url}") from None
    except requests.exceptions.RequestException as e:
        raise ProcessorException(f"Erro de rede: {e}") from e

    try:
        reader = PdfReader(io.BytesIO(response.content))
        return len(reader.pages)
    except Exception as e:
        raise ProcessorException(f"PDF inválido ou corrompido: {e}") from e
