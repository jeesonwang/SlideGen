#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_DIR="$ROOT_DIR/web"

BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-7860}"
FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
BACKEND_ENV_FILE="${BACKEND_ENV_FILE:-$ROOT_DIR/.env}"

BACKEND_PID=""
FRONTEND_PID=""

terminate_tree() {
  local pid="$1"
  local child

  if [[ -z "$pid" ]]; then
    return
  fi

  for child in $(pgrep -P "$pid" 2>/dev/null || true); do
    terminate_tree "$child"
  done

  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
  fi
}

cleanup() {
  local exit_code=$?

  trap - INT TERM EXIT

  terminate_tree "$FRONTEND_PID"
  terminate_tree "$BACKEND_PID"

  wait "$FRONTEND_PID" "$BACKEND_PID" 2>/dev/null || true
  exit "$exit_code"
}

wait_for_processes() {
  while true; do
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
      wait "$BACKEND_PID" 2>/dev/null || return $?
      return 0
    fi

    if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
      wait "$FRONTEND_PID" 2>/dev/null || return $?
      return 0
    fi

    sleep 1
  done
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

trap cleanup INT TERM EXIT

require_command uv
require_command npm

echo "Starting SlideGen backend at http://127.0.0.1:$BACKEND_PORT"
(
  cd "$ROOT_DIR"
  uv run uvicorn slidegen.server:app \
    --host "$BACKEND_HOST" \
    --port "$BACKEND_PORT" \
    --env-file "$BACKEND_ENV_FILE" \
    --reload \
    --reload-exclude test \
    --reload-exclude web
) &
BACKEND_PID=$!

echo "Starting SlideGen frontend at http://127.0.0.1:$FRONTEND_PORT"
(
  cd "$WEB_DIR"
  npm run dev -- --host "$FRONTEND_HOST" --port "$FRONTEND_PORT"
) &
FRONTEND_PID=$!

wait_for_processes
