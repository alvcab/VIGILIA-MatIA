#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FACE_ENV_PYTHON="$HOME/miniforge3/envs/vigilia-face/bin/python"
DEFAULT_AUDIO_PATH="/tmp/vecino.wav"

if [[ ! -x "$FACE_ENV_PYTHON" ]]; then
  echo "No se encontro el entorno vigilia-face en: $FACE_ENV_PYTHON"
  exit 1
fi

AUDIO_PATH="${1:-$DEFAULT_AUDIO_PATH}"

if [[ ! -f "$AUDIO_PATH" ]]; then
  echo "No se encontro el archivo de audio: $AUDIO_PATH"
  echo "Uso:"
  echo "  ./run_vigilia.sh /ruta/al/audio.wav"
  echo
  echo "Si quieres usar el valor por defecto, primero crea /tmp/vecino.wav."
  exit 1
fi

cd "$PROJECT_DIR"
exec "$FACE_ENV_PYTHON" v1_sin_IA/puente_vigilia.py "$AUDIO_PATH"
