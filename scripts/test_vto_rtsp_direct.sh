#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/vigilia_env.sh"

VTO_AUDIO_IP="${VTO_AUDIO_IP:-192.168.100.108}"
VTO_AUDIO_USER="${VTO_AUDIO_USER:-admin}"
VTO_AUDIO_PASS="${VTO_AUDIO_PASS:-Splitreset6901}"
VTO_AUDIO_RTSP_PORT="${VTO_AUDIO_RTSP_PORT:-554}"
VTO_AUDIO_CHANNEL="${VTO_AUDIO_CHANNEL:-1}"
VTO_AUDIO_SUBTYPE="${VTO_AUDIO_SUBTYPE:-0}"
CAPTURE_SECONDS="${1:-10}"
OUTPUT_PATH="${2:-/tmp/vto_rtsp_direct.wav}"
PLAYBACK_GAIN_DB="${VTO_DIRECT_TEST_PLAYBACK_GAIN_DB:-18}"
BOOSTED_OUTPUT_PATH="${OUTPUT_PATH%.wav}_boost.wav"

build_rtsp_url() {
  printf 'rtsp://%s:%s@%s:%s/cam/realmonitor?channel=%s&subtype=%s' \
    "$VTO_AUDIO_USER" \
    "$VTO_AUDIO_PASS" \
    "$VTO_AUDIO_IP" \
    "$VTO_AUDIO_RTSP_PORT" \
    "$VTO_AUDIO_CHANNEL" \
    "$VTO_AUDIO_SUBTYPE"
}

RTSP_URL="$(build_rtsp_url)"

echo "Capturando RTSP directo por ${CAPTURE_SECONDS}s..."
echo "Aprieta el boton del VTO y habla durante la ventana de captura."
echo "output: $OUTPUT_PATH"

ffmpeg \
  -y \
  -rtsp_transport tcp \
  -i "$RTSP_URL" \
  -vn \
  -t "$CAPTURE_SECONDS" \
  -acodec pcm_s16le \
  -ar 16000 \
  -ac 1 \
  "$OUTPUT_PATH"

echo
echo "Resumen:"
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 "$OUTPUT_PATH"
ffmpeg -i "$OUTPUT_PATH" -af volumedetect -f null - 2>&1 | grep -E "mean_volume|max_volume" || true

echo
echo "Generando copia con ganancia suave de +${PLAYBACK_GAIN_DB}dB..."
ffmpeg -y -i "$OUTPUT_PATH" -af "volume=${PLAYBACK_GAIN_DB}dB" "$BOOSTED_OUTPUT_PATH" >/dev/null 2>&1 || true

echo
echo "Reproduciendo audio crudo..."
afplay "$OUTPUT_PATH" || true

if [[ -f "$BOOSTED_OUTPUT_PATH" ]]; then
  echo
  echo "Reproduciendo audio con ganancia..."
  afplay "$BOOSTED_OUTPUT_PATH" || true
fi
