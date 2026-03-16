"""
Registro central de scrapers disponíveis.
Para adicionar novo portal: importar e registrar aqui.
"""
from app.scrapers.base import BaseScraper
from app.scrapers.goiania import GoianiaScraper

_REGISTRY: dict[str, BaseScraper] = {
    "goiania": GoianiaScraper(),
}


def get_scraper(portal_id: str) -> BaseScraper:
    scraper = _REGISTRY.get(portal_id)
    if not scraper:
        raise KeyError(f"Portal '{portal_id}' não encontrado. Disponíveis: {list(_REGISTRY.keys())}")
    return scraper


def list_portals() -> list[str]:
    return list(_REGISTRY.keys())
