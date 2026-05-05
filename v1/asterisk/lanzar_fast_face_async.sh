#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_DIR/scripts/vigilia_env.sh"

FLAG_PATH="${1:-}"
LOG_PATH="${2:-$VIGILIA_ASTERISK_LOG_PATH}"
RESPONSE_AUDIO_PATH="${3:-$VIGILIA_DEFAULT_RESPONSE_AUDIO_PATH}"
HELLO_FLAG_PATH="${4:-}"
DONE_FLAG_PATH="${5:-}"

if [[ -z "$FLAG_PATH" ]]; then
  exit 1
fi

mkdir -p "$(dirname "$LOG_PATH")"

{
  echo "[FAST_FACE] $(date '+%Y-%m-%d %H:%M:%S') launching_async"
} >> "$LOG_PATH" 2>&1

nohup "$PROJECT_DIR/v1/asterisk/verificar_residente_inmediato.sh" \
  "$FLAG_PATH" \
  "$LOG_PATH" \
  "$RESPONSE_AUDIO_PATH" \
  "$HELLO_FLAG_PATH" \
  "$DONE_FLAG_PATH" >/dev/null 2>&1 &
