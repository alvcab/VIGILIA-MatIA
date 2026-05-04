#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/vigilia_env.sh"

FACE_ENV_PYTHON="${FACE_ENV_PYTHON:-$HOME/miniforge3/envs/vigilia-face/bin/python}"

if [[ ! -x "$FACE_ENV_PYTHON" ]]; then
  echo "Face env no disponible: $FACE_ENV_PYTHON" >&2
  exit 1
fi

if [[ -S "$VIGILIA_FACE_SERVICE_SOCKET" ]]; then
  echo "Face service ya disponible en $VIGILIA_FACE_SERVICE_SOCKET"
  exit 0
fi

nohup "$FACE_ENV_PYTHON" "$PROJECT_DIR/v1/face_service.py" >> "$VIGILIA_FACE_SERVICE_LOG" 2>&1 &

for _ in $(seq 1 30); do
  if [[ -S "$VIGILIA_FACE_SERVICE_SOCKET" ]]; then
    echo "Face service listo."
    exit 0
  fi
  sleep 0.2
done

echo "Face service no inició a tiempo." >&2
exit 1
