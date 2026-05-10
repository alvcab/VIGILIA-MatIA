#!/usr/bin/env bash
set -euo pipefail

OUTPUT_PATH="${1:-runtime/voice/matia-reference.wav}"
DURATION_SECONDS="${VIGILIA_VOICE_SAMPLE_SECONDS:-30}"

mkdir -p "$(dirname "${OUTPUT_PATH}")"

echo "Grabando muestra de voz para MatIA por ${DURATION_SECONDS}s."
echo "Texto sugerido:"
echo "Hola, soy MatIA. Estoy probando mi voz para el control de acceso."
echo "Rostro identificado. Abriendo el porton. Un momento, por favor."

ffmpeg -y \
  -f avfoundation \
  -i ":0" \
  -t "${DURATION_SECONDS}" \
  -ar 24000 \
  -ac 1 \
  -acodec pcm_s16le \
  "${OUTPUT_PATH}"

echo "Muestra guardada en ${OUTPUT_PATH}"
