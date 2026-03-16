#!/bin/bash
# Uso: ./scripts/run_scraper.sh goiania 2025
PORTAL=${1:-goiania}
ANO=${2:-2025}
docker compose exec backend python -m app.scrapers.runner --portal "$PORTAL" --ano "$ANO"
