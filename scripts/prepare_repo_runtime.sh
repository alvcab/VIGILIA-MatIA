#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$SCRIPT_DIR/vigilia_env.sh"

python3 "$SCRIPT_DIR/prepare_repo_runtime.py"
"$PROJECT_DIR/v1_sin_IA/asterisk/preparar_saludo_vigilia.sh" "Hola. Por favor espere." "${VIGILIA_PROMPT_AUDIO_BASE}.wav" >/dev/null

ffmpeg -y -f lavfi -i "sine=frequency=880:sample_rate=8000:duration=0.18" -ac 1 "${VIGILIA_LISTEN_AUDIO_BASE}.wav" >/dev/null 2>&1
ffmpeg -y -i "${VIGILIA_LISTEN_AUDIO_BASE}.wav" -f alaw -ar 8000 -ac 1 "${VIGILIA_LISTEN_AUDIO_BASE}.alaw" >/dev/null 2>&1
ffmpeg -y -i "${VIGILIA_LISTEN_AUDIO_BASE}.wav" -f mulaw -ar 8000 -ac 1 "${VIGILIA_LISTEN_AUDIO_BASE}.ulaw" >/dev/null 2>&1
