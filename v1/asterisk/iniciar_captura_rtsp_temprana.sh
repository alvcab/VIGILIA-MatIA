#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_DIR/scripts/vigilia_env.sh"

AUDIO_BASE="${1:-}"
LOG_PATH="${2:-$VIGILIA_ASTERISK_LOG_PATH}"
VTO_AUDIO_IP="${VTO_AUDIO_IP:-192.168.100.108}"
VTO_AUDIO_USER="${VTO_AUDIO_USER:-admin}"
VTO_AUDIO_PASS="${VTO_AUDIO_PASS:-Splitreset6901}"
VTO_AUDIO_RTSP_PORT="${VTO_AUDIO_RTSP_PORT:-554}"
VTO_AUDIO_CHANNEL="${VTO_AUDIO_CHANNEL:-1}"
VTO_AUDIO_SUBTYPE="${VTO_AUDIO_SUBTYPE:-0}"
VTO_EARLY_AUDIO_SECONDS="${VTO_EARLY_AUDIO_SECONDS:-3}"

if [[ -z "$AUDIO_BASE" ]]; then
  exit 1
fi

mkdir -p "$(dirname "$LOG_PATH")"
RTSP_AUDIO_PATH="${AUDIO_BASE}_rtsp.wav"

build_rtsp_url() {
  printf 'rtsp://%s:%s@%s:%s/cam/realmonitor?channel=%s&subtype=%s' \
    "$VTO_AUDIO_USER" \
    "$VTO_AUDIO_PASS" \
    "$VTO_AUDIO_IP" \
    "$VTO_AUDIO_RTSP_PORT" \
    "$VTO_AUDIO_CHANNEL" \
    "$VTO_AUDIO_SUBTYPE"
}

{
  echo "[EARLY_RTSP] $(date '+%Y-%m-%d %H:%M:%S') starting path=$RTSP_AUDIO_PATH seconds=$VTO_EARLY_AUDIO_SECONDS"
} >> "$LOG_PATH" 2>&1

nohup ffmpeg \
  -y \
  -rtsp_transport tcp \
  -i "$(build_rtsp_url)" \
  -vn \
  -t "$VTO_EARLY_AUDIO_SECONDS" \
  -acodec pcm_s16le \
  -ar 16000 \
  -ac 1 \
  "$RTSP_AUDIO_PATH" >> "$LOG_PATH" 2>&1 &
