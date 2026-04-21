#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "Starting online deployment..."

if ! command -v docker >/dev/null 2>&1; then
  echo "[ERROR] docker command not found."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "[ERROR] Docker daemon is not running."
  exit 1
fi

if [ ! -f .env.online ]; then
  echo "[WARN] .env.online not found. Creating from .env.online.example"
  cp .env.online.example .env.online
  echo "[WARN] Please edit .env.online first, then run this script again."
  exit 1
fi

llm_api_key="$(grep -E '^\s*LLM_API_KEY\s*=' .env.online | head -n1 | cut -d'=' -f2- | tr -d '[:space:]' || true)"
if [ -z "$llm_api_key" ]; then
  echo "[WARN] LLM_API_KEY is empty in .env.online. AI feedback generation may fail."
fi

if ! docker compose -f docker-compose.online.yml --env-file .env.online up -d --build; then
  echo "[WARN] Build startup failed. Trying cached images with --no-build..."
  docker compose -f docker-compose.online.yml --env-file .env.online up -d --no-build
fi

echo "Running migrations..."
docker compose -f docker-compose.online.yml --env-file .env.online exec -T backend alembic upgrade head

echo "Online deployment completed."
echo "Open: http://<your-server-ip>/"
