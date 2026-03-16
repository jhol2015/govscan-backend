from datetime import date, datetime
from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Diario(Base):
    __tablename__ = "diarios"

    id:           Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    portal:       Mapped[str]      = mapped_column(String(100), nullable=False, index=True)
    municipio:    Mapped[str]      = mapped_column(String(200), nullable=False)
    edicao:       Mapped[str]      = mapped_column(String(20),  nullable=False)
    data_edicao:  Mapped[date]     = mapped_column(Date,        nullable=False, index=True)
    tipo:         Mapped[str]      = mapped_column(String(50),  nullable=False, default="Normal")
    paginas:      Mapped[int|None] = mapped_column(Integer,     nullable=True)
    url:          Mapped[str]      = mapped_column(String(500), nullable=False, unique=True)
    nome_arquivo: Mapped[str]      = mapped_column(String(200), nullable=False)
    status:       Mapped[str]      = mapped_column(String(20),  nullable=False, default="pending")
    erro:         Mapped[str|None] = mapped_column(String(500), nullable=True)
    criado_em:    Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em:Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
