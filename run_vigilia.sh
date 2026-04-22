#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FACE_ENV_PYTHON="$HOME/miniforge3/envs/vigilia-face/bin/python"
DEFAULT_AUDIO_PATH="/tmp/vecino.wav"
INFERENCE_SOCKET_PATH="/tmp/vigilia_inference.sock"
INFERENCE_LOG_PATH="/tmp/vigilia_inference.log"
INFERENCE_CLIENT_SCRIPT="$PROJECT_DIR/v1_sin_IA/inference_client.py"

if [[ ! -x "$FACE_ENV_PYTHON" ]]; then
  echo "No se encontro el entorno vigilia-face en: $FACE_ENV_PYTHON"
  exit 1
fi

AUDIO_PATH="${1:-$DEFAULT_AUDIO_PATH}"
RESPONSE_AUDIO_PATH="${2:-/tmp/ia_dice.wav}"

if [[ ! -f "$AUDIO_PATH" ]]; then
  echo "No se encontro el archivo de audio: $AUDIO_PATH"
  echo "Uso:"
  echo "  ./run_vigilia.sh /ruta/al/audio.wav [/ruta/a/respuesta.wav]"
  echo
  echo "Si quieres usar el valor por defecto, primero crea /tmp/vecino.wav."
  exit 1
fi

check_inference_service() {
  "$FACE_ENV_PYTHON" "$INFERENCE_CLIENT_SCRIPT" health 1 >/dev/null 2>&1
}

start_inference_service() {
  nohup "$FACE_ENV_PYTHON" "$PROJECT_DIR/v1_sin_IA/inference_service.py" >> "$INFERENCE_LOG_PATH" 2>&1 &

  for _ in {1..20}; do
    if [[ -S "$INFERENCE_SOCKET_PATH" ]] && check_inference_service; then
      break
    fi
    sleep 0.2
  done
}

if [[ -S "$INFERENCE_SOCKET_PATH" ]] && ! check_inference_service; then
  rm -f "$INFERENCE_SOCKET_PATH"
fi

if [[ ! -S "$INFERENCE_SOCKET_PATH" ]]; then
  start_inference_service
fi

if ! check_inference_service; then
  export VIGILIA_DISABLE_INFERENCE_SERVICE=1
  echo "[VIGILIA] inference service unavailable, using local fallback"
fi

cd "$PROJECT_DIR"
exec "$FACE_ENV_PYTHON" v1_sin_IA/puente_vigilia.py "$AUDIO_PATH" "$RESPONSE_AUDIO_PATH"
