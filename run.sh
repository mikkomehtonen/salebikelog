#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$SCRIPT_DIR/uploads"
mkdir -p "$SCRIPT_DIR/database"

docker rm -f salebikelog 2>/dev/null || true

docker run -d \
  --name salebikelog \
  --network host \
  --restart unless-stopped \
  -v "$SCRIPT_DIR/uploads:/app/uploads" \
  -v "$SCRIPT_DIR/database:/app/database" \
  -e LM_STUDIO_URL=http://127.0.0.1:1234/v1/ \
  -e LM_STUDIO_MODEL=qwen/qwen3.6-35b-a3b \
  -e DB_PATH=/app/database/trips.db \
  salebikelog
