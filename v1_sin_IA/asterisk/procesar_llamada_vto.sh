#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
RUN_VIGILIA_SCRIPT="$PROJECT_DIR/run_vigilia.sh"

AUDIO_PATH="${1:-}"
RESPONSE_AUDIO_PATH="${2:-}"
LOG_PATH="${3:-/tmp/vigilia_asterisk.log}"
CALL_ID="$(basename "${AUDIO_PATH%.*}" 2>/dev/null || echo unknown)"

log_state() {
  local state="$1"
  echo "[VIGILIA] $(date '+%Y-%m-%d %H:%M:%S') call_id=$CALL_ID state=$state"
}

if [[ -z "$AUDIO_PATH" || -z "$RESPONSE_AUDIO_PATH" ]]; then
  echo "[VIGILIA] Uso: procesar_llamada_vto.sh <audio.wav> <respuesta.wav> [log]" >> "$LOG_PATH"
  exit 1
fi

mkdir -p "$(dirname "$LOG_PATH")"

{
  log_state "received"
  echo "[VIGILIA] audio=$AUDIO_PATH"
  echo "[VIGILIA] response=$RESPONSE_AUDIO_PATH"

  if [[ ! -x "$RUN_VIGILIA_SCRIPT" ]]; then
    echo "[VIGILIA] run_vigilia.sh no es ejecutable: $RUN_VIGILIA_SCRIPT"
    exit 1
  fi

  log_state "processing"
  "$RUN_VIGILIA_SCRIPT" "$AUDIO_PATH" "$RESPONSE_AUDIO_PATH"

  if [[ -f "$RESPONSE_AUDIO_PATH" ]]; then
    log_state "response_ready"
    echo "[VIGILIA] respuesta generada correctamente"
  else
    log_state "response_missing"
    echo "[VIGILIA] no se genero audio de respuesta"
  fi
  log_state "completed"
} >> "$LOG_PATH" 2>&1
