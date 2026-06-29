#!/usr/bin/env bash
# Wrapper para searxng-mcp.py
# Carga .env si existe, luego ejecuta el MCP

DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$DIR/.env"

if [ -f "$ENV_FILE" ]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

exec python3 "$DIR/bin/searxng-mcp.py"
