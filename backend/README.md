# GovScan — Backend

API REST para extração e indexação de Diários Oficiais municipais.

## Stack
- Python 3.12 + FastAPI
- SQLAlchemy (async) + Alembic
- PostgreSQL 16
- pypdf + BeautifulSoup4

## Desenvolvimento local

```bash
cp ../.env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Docs: http://localhost:8000/docs

## Via Docker (ambiente separado)

```bash
docker build -t govscan-backend .
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/govscan \
  govscan-backend
```

## Executar scraper manualmente

```bash
python -m app.scrapers.runner --portal goiania --ano 2025
```

## Testes

```bash
pytest tests/
```

## Adicionar novo portal

1. Crie `app/scrapers/seu_municipio.py` herdando `BaseScraper`
2. Registre em `app/scrapers/registry.py`
3. Adicione entrada em `../config/portals.yaml`
