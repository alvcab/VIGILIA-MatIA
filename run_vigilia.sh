#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$PROJECT_DIR/scripts/vigilia_env.sh"
FACE_ENV_PYTHON="$HOME/miniforge3/envs/vigilia-face/bin/python"
DEFAULT_AUDIO_PATH="$VIGILIA_DEFAULT_AUDIO_PATH"
INFERENCE_SOCKET_PATH="$VIGILIA_INFERENCE_SOCKET"
INFERENCE_LOG_PATH="$VIGILIA_INFERENCE_LOG"

if [[ ! -x "$FACE_ENV_PYTHON" ]]; then
  echo "No se encontro el entorno vigilia-face en: $FACE_ENV_PYTHON"
  exit 1
fi

AUDIO_PATH="${1:-$DEFAULT_AUDIO_PATH}"
RESPONSE_AUDIO_PATH="${2:-$VIGILIA_DEFAULT_RESPONSE_AUDIO_PATH}"

if [[ ! -f "$AUDIO_PATH" ]]; then
  echo "No se encontro el archivo de audio: $AUDIO_PATH"
  echo "Uso:"
  echo "  ./run_vigilia.sh /ruta/al/audio.wav [/ruta/a/respuesta.wav]"
  echo
  echo "Si quieres usar el valor por defecto, primero crea $DEFAULT_AUDIO_PATH."
  exit 1
fi

start_inference_service() {
  nohup "$FACE_ENV_PYTHON" "$PROJECT_DIR/v1_sin_IA/inference_service.py" >> "$INFERENCE_LOG_PATH" 2>&1 &
}

if [[ ! -S "$INFERENCE_SOCKET_PATH" ]]; then
  start_inference_service
fi

cd "$PROJECT_DIR"
exec "$FACE_ENV_PYTHON" v1_sin_IA/puente_vigilia.py "$AUDIO_PATH" "$RESPONSE_AUDIO_PATH"
