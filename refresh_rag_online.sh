#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.online.yml}"
ENV_FILE="${ENV_FILE:-.env.online}"
RAG_DIR="${1:-rag_materials}"

compose() {
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" "$@"
}

echo "Starting RAG refresh..."

if ! command -v docker >/dev/null 2>&1; then
  echo "[ERROR] docker command not found."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "[ERROR] Docker daemon is not running."
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "[ERROR] $ENV_FILE not found."
  exit 1
fi

echo "Ensuring database and backend are up..."
if ! compose up -d --build db backend; then
  echo "[WARN] Build/start failed. Trying cached images with --no-build..."
  compose up -d --no-build db backend
fi

echo "Checking knowledge base directory inside backend container..."
compose exec -T backend test -d "$RAG_DIR"

echo "Ingesting documents from $RAG_DIR ..."
compose exec -T backend python ingest.py --dir "$RAG_DIR"

echo "Rebuilding embeddings..."
compose exec -T backend python reindex_embeddings.py

echo "Running retrieval check..."
compose exec -T backend python check_retrieval.py

echo "RAG refresh completed."