#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
FACE_ENV_PYTHON="$HOME/miniforge3/envs/vigilia-face/bin/python"
PROMPT_SCRIPT="$PROJECT_DIR/v1_sin_IA/asterisk/preparar_saludo_vigilia.py"

TEXT="${1:-Hola.}"
OUTPUT_PATH="${2:-/tmp/vigilia_prompt.wav}"

if [[ ! -x "$FACE_ENV_PYTHON" ]]; then
  echo "No se encontro el entorno vigilia-face en: $FACE_ENV_PYTHON"
  exit 1
fi

exec "$FACE_ENV_PYTHON" "$PROMPT_SCRIPT" "$TEXT" "$OUTPUT_PATH"
