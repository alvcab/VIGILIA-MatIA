#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_DIR/scripts/vigilia_env.sh"
RUN_VIGILIA_SCRIPT="$PROJECT_DIR/run_vigilia.sh"
VTO_AUDIO_IP="${VTO_AUDIO_IP:-192.168.100.108}"
VTO_AUDIO_USER="${VTO_AUDIO_USER:-admin}"
VTO_AUDIO_PASS="${VTO_AUDIO_PASS:-Splitreset6901}"
VTO_AUDIO_RTSP_PORT="${VTO_AUDIO_RTSP_PORT:-554}"
VTO_AUDIO_CHANNEL="${VTO_AUDIO_CHANNEL:-1}"
VTO_AUDIO_SUBTYPE="${VTO_AUDIO_SUBTYPE:-0}"
VTO_AUDIO_SECONDS="${VTO_AUDIO_SECONDS:-5}"

AUDIO_PATH="${1:-}"
RESPONSE_AUDIO_PATH="${2:-}"
LOG_PATH="${3:-$VIGILIA_ASTERISK_LOG_PATH}"
CALL_ID="$(basename "${AUDIO_PATH%.*}" 2>/dev/null || echo unknown)"
RTSP_AUDIO_PATH="$VIGILIA_AUDIO_DIR/${CALL_ID}_rtsp.wav"

build_rtsp_url() {
  printf 'rtsp://%s:%s@%s:%s/cam/realmonitor?channel=%s&subtype=%s' \
    "$VTO_AUDIO_USER" \
    "$VTO_AUDIO_PASS" \
    "$VTO_AUDIO_IP" \
    "$VTO_AUDIO_RTSP_PORT" \
    "$VTO_AUDIO_CHANNEL" \
    "$VTO_AUDIO_SUBTYPE"
}

capture_rtsp_audio() {
  local rtsp_url
  rtsp_url="$(build_rtsp_url)"

  ffmpeg \
    -y \
    -rtsp_transport tcp \
    -i "$rtsp_url" \
    -vn \
    -t "$VTO_AUDIO_SECONDS" \
    -acodec pcm_s16le \
    -ar 16000 \
    -ac 1 \
    "$RTSP_AUDIO_PATH"
}

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
  echo "[VIGILIA] rtsp_audio=$RTSP_AUDIO_PATH"

  if [[ ! -x "$RUN_VIGILIA_SCRIPT" ]]; then
    echo "[VIGILIA] run_vigilia.sh no es ejecutable: $RUN_VIGILIA_SCRIPT"
    exit 1
  fi

  SELECTED_AUDIO_PATH="$AUDIO_PATH"

  log_state "capturing_rtsp_audio"
  if capture_rtsp_audio >> "$LOG_PATH" 2>&1; then
    RTSP_AUDIO_SIZE="$(wc -c < "$RTSP_AUDIO_PATH" | tr -d ' ')"
    echo "[VIGILIA] rtsp_audio_size=$RTSP_AUDIO_SIZE"
    if [[ "$RTSP_AUDIO_SIZE" -gt 44 ]]; then
      SELECTED_AUDIO_PATH="$RTSP_AUDIO_PATH"
      log_state "using_rtsp_audio"
    else
      echo "[VIGILIA] rtsp audio sin contenido util, se mantiene audio SIP"
      log_state "rtsp_audio_empty"
    fi
  else
    echo "[VIGILIA] fallo captura RTSP, se mantiene audio SIP"
    log_state "rtsp_audio_failed"
  fi

  log_state "processing"
  export VIGILIA_DISABLE_INFERENCE_SERVICE=1
  echo "[VIGILIA] inference_service_disabled_for_vto=1"
  "$RUN_VIGILIA_SCRIPT" "$SELECTED_AUDIO_PATH" "$RESPONSE_AUDIO_PATH"

  if [[ -f "$RESPONSE_AUDIO_PATH" ]]; then
    log_state "response_ready"
    echo "[VIGILIA] respuesta generada correctamente"
  else
    log_state "response_missing"
    echo "[VIGILIA] no se genero audio de respuesta"
  fi
  log_state "completed"
} >> "$LOG_PATH" 2>&1
