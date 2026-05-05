#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_DIR/scripts/vigilia_env.sh"
RUN_VIGILIA_SCRIPT="$PROJECT_DIR/run_vigilia.sh"
CAPTURE_SCRIPT="$PROJECT_DIR/v1/asterisk/capturar_rtsp_hasta_silencio.py"
VTO_AUDIO_IP="${VTO_AUDIO_IP:-192.168.100.108}"
VTO_AUDIO_USER="${VTO_AUDIO_USER:-admin}"
VTO_AUDIO_PASS="${VTO_AUDIO_PASS:-Splitreset6901}"
VTO_AUDIO_RTSP_PORT="${VTO_AUDIO_RTSP_PORT:-554}"
VTO_AUDIO_CHANNEL="${VTO_AUDIO_CHANNEL:-1}"
VTO_AUDIO_SUBTYPE="${VTO_AUDIO_SUBTYPE:-0}"
VTO_AUDIO_SECONDS="${VTO_AUDIO_SECONDS:-3}"

AUDIO_PATH="${1:-}"
RESPONSE_AUDIO_PATH="${2:-}"
LOG_PATH="${3:-$VIGILIA_ASTERISK_LOG_PATH}"
FAST_FACE_FLAG_PATH="${4:-}"
FAST_FACE_DONE_FLAG_PATH="${5:-}"
CALL_ID="$(basename "${AUDIO_PATH%.*}" 2>/dev/null || echo unknown)"
RTSP_AUDIO_PATH="$VIGILIA_AUDIO_DIR/${CALL_ID}_rtsp.wav"
FAST_FACE_GRACE_ATTEMPTS="${VIGILIA_FAST_FACE_GRACE_ATTEMPTS:-12}"
FAST_FACE_GRACE_SLEEP_SECONDS="${VIGILIA_FAST_FACE_GRACE_SLEEP_SECONDS:-0.05}"
EARLY_RTSP_WAIT_ATTEMPTS="${VTO_EARLY_AUDIO_WAIT_ATTEMPTS:-70}"

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

  python3 "$CAPTURE_SCRIPT" \
    --rtsp-url "$rtsp_url" \
    --output "$RTSP_AUDIO_PATH" \
    --max-seconds "$VTO_AUDIO_SECONDS" \
    --log-prefix "[RTSP_CAPTURE]"
}

wait_for_existing_rtsp_audio() {
  local attempts="${1:-$EARLY_RTSP_WAIT_ATTEMPTS}"
  local attempt=0

  while (( attempt < attempts )); do
    if [[ -f "$RTSP_AUDIO_PATH" ]]; then
      local size
      size="$(wc -c < "$RTSP_AUDIO_PATH" | tr -d ' ' || echo 0)"
      if [[ "$size" -gt 44 ]]; then
        return 0
      fi
    fi
    sleep 0.05
    attempt=$((attempt + 1))
  done

  return 1
}

log_state() {
  local state="$1"
  echo "[VIGILIA] $(date '+%Y-%m-%d %H:%M:%S') call_id=$CALL_ID state=$state"
}

wait_for_fast_face_grace_window() {
  local attempt=0

  while (( attempt < FAST_FACE_GRACE_ATTEMPTS )); do
    if [[ -n "$FAST_FACE_FLAG_PATH" && -f "$FAST_FACE_FLAG_PATH" ]]; then
      return 0
    fi
    if [[ -n "$FAST_FACE_DONE_FLAG_PATH" && -f "$FAST_FACE_DONE_FLAG_PATH" ]]; then
      return 1
    fi
    sleep "$FAST_FACE_GRACE_SLEEP_SECONDS"
    attempt=$((attempt + 1))
  done

  return 1
}

if [[ -z "$RESPONSE_AUDIO_PATH" ]]; then
  echo "[VIGILIA] Uso: procesar_llamada_vto.sh <audio.wav> <respuesta.wav> [log]" >> "$LOG_PATH"
  exit 1
fi

mkdir -p "$(dirname "$LOG_PATH")"

{
  log_state "received"
  echo "[VIGILIA] audio=$AUDIO_PATH"
  echo "[VIGILIA] response=$RESPONSE_AUDIO_PATH"
  echo "[VIGILIA] rtsp_audio=$RTSP_AUDIO_PATH"
  echo "[VIGILIA] fast_face_grace_attempts=$FAST_FACE_GRACE_ATTEMPTS"
  echo "[VIGILIA] fast_face_grace_sleep_seconds=$FAST_FACE_GRACE_SLEEP_SECONDS"
  echo "[VIGILIA] early_rtsp_wait_attempts=$EARLY_RTSP_WAIT_ATTEMPTS"

  if [[ ! -x "$RUN_VIGILIA_SCRIPT" ]]; then
    echo "[VIGILIA] run_vigilia.sh no es ejecutable: $RUN_VIGILIA_SCRIPT"
    exit 1
  fi

  if wait_for_fast_face_grace_window; then
    echo "[VIGILIA] fast_face_opened_during_grace=1"
    log_state "fast_face_opened"
    exit 0
  fi

  SELECTED_AUDIO_PATH=""
  if [[ -n "$AUDIO_PATH" && -f "$AUDIO_PATH" ]]; then
    SELECTED_AUDIO_PATH="$AUDIO_PATH"
  fi

  log_state "capturing_rtsp_audio"
  if wait_for_existing_rtsp_audio "$EARLY_RTSP_WAIT_ATTEMPTS"; then
    RTSP_AUDIO_SIZE="$(wc -c < "$RTSP_AUDIO_PATH" | tr -d ' ')"
    echo "[VIGILIA] rtsp_audio_size=$RTSP_AUDIO_SIZE"
    SELECTED_AUDIO_PATH="$RTSP_AUDIO_PATH"
    log_state "using_early_rtsp_audio"
  elif capture_rtsp_audio >> "$LOG_PATH" 2>&1; then
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

  if [[ -z "$SELECTED_AUDIO_PATH" || ! -f "$SELECTED_AUDIO_PATH" ]]; then
    echo "[VIGILIA] no audio source available for processing"
    log_state "audio_missing"
    exit 1
  fi

  log_state "processing"
  # Keep the resident Whisper service enabled here to avoid paying model load
  # time on every VTO call. The second-stage voice flow otherwise takes too
  # long and the visitor hears no timely response.
  export VIGILIA_DISABLE_INFERENCE_SERVICE=0
  if [[ -z "$FAST_FACE_FLAG_PATH" && -z "$FAST_FACE_DONE_FLAG_PATH" ]]; then
    export VIGILIA_INFERENCE_SERVICE_TIMEOUT_SECONDS=2
  else
    export VIGILIA_INFERENCE_SERVICE_TIMEOUT_SECONDS=4
  fi
  export VIGILIA_DISABLE_LOCAL_TRANSCRIPTION_FALLBACK=1
  export VIGILIA_AUDIO_SIZE_SHORT_CIRCUIT_BYTES=5000
  export VIGILIA_SILENT_AUDIO_SHORT_CIRCUIT_DB=-58
  if [[ -z "$FAST_FACE_FLAG_PATH" && -z "$FAST_FACE_DONE_FLAG_PATH" ]]; then
    export VIGILIA_DISABLE_VTO_SNAPSHOT=1
  else
    export VIGILIA_DISABLE_VTO_SNAPSHOT=0
  fi
  export VIGILIA_ENABLE_LOCAL_FOLLOWUP_CAPTURE=0
  export VIGILIA_PLAY_RESPONSE_LOCALLY=1
  export VIGILIA_SKIP_RESPONSE_AUDIO_RENDER=1
  echo "[VIGILIA] inference_service_disabled_for_vto=0"
  echo "[VIGILIA] inference_service_timeout_seconds=$VIGILIA_INFERENCE_SERVICE_TIMEOUT_SECONDS"
  echo "[VIGILIA] local_transcription_fallback_disabled=$VIGILIA_DISABLE_LOCAL_TRANSCRIPTION_FALLBACK"
  echo "[VIGILIA] audio_size_short_circuit_bytes=$VIGILIA_AUDIO_SIZE_SHORT_CIRCUIT_BYTES"
  echo "[VIGILIA] silent_audio_short_circuit_db=$VIGILIA_SILENT_AUDIO_SHORT_CIRCUIT_DB"
  echo "[VIGILIA] disable_vto_snapshot=$VIGILIA_DISABLE_VTO_SNAPSHOT"
  echo "[VIGILIA] play_response_locally=$VIGILIA_PLAY_RESPONSE_LOCALLY"
  echo "[VIGILIA] skip_response_audio_render=$VIGILIA_SKIP_RESPONSE_AUDIO_RENDER"
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
