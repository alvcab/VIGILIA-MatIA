#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$PROJECT_DIR/scripts/vigilia_env.sh"

DURATION_SECONDS="${1:-2}"
MIC_DEVICE_SPEC="${VIGILIA_LOCAL_FOLLOWUP_AUDIO_DEVICE:-1}"
OUTPUT_PATH="$(mktemp /tmp/vigilia_local_turno.XXXXXX.wav)"

capture_with_command() {
  local -a cmd=("$@")

  if "${cmd[@]}" >/dev/null 2>&1 && [[ -s "$OUTPUT_PATH" ]]; then
    return 0
  fi

  return 1
}

try_capture_local_turn() {
  local normalized_spec="$MIC_DEVICE_SPEC"
  normalized_spec="${normalized_spec#:}"

  if [[ "$normalized_spec" =~ ^[0-9]+$ ]]; then
    if capture_with_command \
      ffmpeg -y -f avfoundation -audio_device_index "$normalized_spec" -i "" \
      -t "$DURATION_SECONDS" -ar 16000 -ac 1 "$OUTPUT_PATH"; then
      return 0
    fi
  fi

  if capture_with_command \
    ffmpeg -y -f avfoundation -i ":Built-in Microphone" \
    -t "$DURATION_SECONDS" -ar 16000 -ac 1 "$OUTPUT_PATH"; then
    return 0
  fi

  if capture_with_command \
    ffmpeg -y -f avfoundation -i ":1" \
    -t "$DURATION_SECONDS" -ar 16000 -ac 1 "$OUTPUT_PATH"; then
    return 0
  fi

  return 1
}

echo "Grabando turno local durante ${DURATION_SECONDS}s..."
if ! try_capture_local_turn; then
  echo "No pude grabar audio local con ffmpeg."
  echo "Prueba revisar los dispositivos con:"
  echo "  ffmpeg -f avfoundation -list_devices true -i \"\""
  exit 1
fi

echo "Audio capturado en $OUTPUT_PATH"
exec "$PROJECT_DIR/run_vigilia.sh" "$OUTPUT_PATH"
