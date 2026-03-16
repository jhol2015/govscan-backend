# GovScan

Plataforma genérica de extração e monitoramento de Diários Oficiais municipais.

## Stack
- **Backend**: Python 3.12 · FastAPI · SQLAlchemy · Alembic
- **Frontend**: React 18 · TypeScript · Vite
- **Banco**: PostgreSQL 16
- **Infra**: Docker · Docker Compose · Nginx

## Subir o projeto

```bash
cp .env.example .env
docker compose up --build
```

- API:      http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Executar scraper manualmente

```bash
docker compose exec backend python -m app.scrapers.runner --portal goiania --ano 2025
```
