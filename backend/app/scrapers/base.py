"""
Contrato que todo scraper de portal deve implementar.
Adicionar um novo município = criar um novo arquivo herdando BaseScraper.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass
class DiarioRaw:
    """Dados extraídos da página antes de qualquer processamento."""
    portal:       str
    municipio:    str
    edicao:       str
    data_edicao:  date
    tipo:         str
    url:          str
    nome_arquivo: str


class BaseScraper(ABC):
    @abstractmethod
    def extrair_links(self, ano: int) -> list[DiarioRaw]:
        """Acessa a página do portal e retorna a lista de diários encontrados."""
        ...

    @property
    @abstractmethod
    def portal_id(self) -> str:
        """Identificador único do portal, ex: 'goiania'."""
        ...
