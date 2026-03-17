from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class DiarioBase(BaseModel):
    portal:       str
    municipio:    str
    edicao:       str
    data_edicao:  date
    tipo:         str
    url:          str
    nome_arquivo: str


class DiarioCreate(DiarioBase):
    pass


class DiarioUpdate(BaseModel):
    paginas:  Optional[int]  = None
    status:   Optional[str]  = None
    erro:     Optional[str]  = None


class DiarioResponse(DiarioBase):
    id:           int
    paginas:      Optional[int]
    status:       str
    erro:         Optional[str]
    criado_em:    datetime
    atualizado_em:datetime

    model_config = {"from_attributes": True}


class DiarioListResponse(BaseModel):
    total:  int
    items:  list[DiarioResponse]


class SincronizacaoProgressoResponse(BaseModel):
    portal: str
    ano: int
    total: int
    processados: int
    ok: int
    erros: int
    pendentes: int
    progresso: int
    status: str
    mensagem: str | None = None
