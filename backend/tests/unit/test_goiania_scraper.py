from datetime import date
from app.scrapers.goiania import GoianiaScraper


def test_parsear_nome_normal():
    edicao, data, tipo = GoianiaScraper._parsear_nome("do_20251230_000008691.pdf")
    assert edicao == "8691"
    assert data == date(2025, 12, 30)
    assert tipo == "Normal"


def test_parsear_nome_edicao_extra():
    _, _, tipo = GoianiaScraper._parsear_nome("do_20251223_000008689_edi.pdf")
    assert tipo == "Edição Extra"


def test_parsear_nome_suplemento():
    _, _, tipo = GoianiaScraper._parsear_nome("do_20250203_000008470_suplemento.pdf")
    assert tipo == "Suplemento"
