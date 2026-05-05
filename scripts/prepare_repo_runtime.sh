#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

source "$SCRIPT_DIR/vigilia_env.sh"

python3 "$SCRIPT_DIR/prepare_repo_runtime.py"
"$PROJECT_DIR/v1/asterisk/preparar_saludo_vigilia.sh" "${VIGILIA_VTO_LOCAL_HELLO_TEXT}" "${VIGILIA_HELLO_AUDIO_PATH}" >/dev/null
HELLO_TMP_PATH="${VIGILIA_HELLO_AUDIO_PATH%.wav}_trimmed.wav"
ffmpeg -y -i "${VIGILIA_HELLO_AUDIO_PATH}" -af "silenceremove=start_periods=1:start_silence=0.02:start_threshold=-38dB,areverse,silenceremove=start_periods=1:start_silence=0.02:start_threshold=-38dB,areverse,atempo=1.25" "$HELLO_TMP_PATH" >/dev/null 2>&1
mv "$HELLO_TMP_PATH" "${VIGILIA_HELLO_AUDIO_PATH}"
"$PROJECT_DIR/v1/asterisk/preparar_saludo_vigilia.sh" "Hola. Por favor espere." "${VIGILIA_PROMPT_AUDIO_BASE}.wav" >/dev/null
"$PROJECT_DIR/v1/asterisk/preparar_saludo_vigilia.sh" "No pude escucharte bien. Por favor, pulsa el boton de nuevo." "${VIGILIA_RETRY_AUDIO_PATH}" >/dev/null

ffmpeg -y -f lavfi -i "sine=frequency=880:sample_rate=8000:duration=0.18" -ac 1 "${VIGILIA_LISTEN_AUDIO_BASE}.wav" >/dev/null 2>&1
ffmpeg -y -i "${VIGILIA_LISTEN_AUDIO_BASE}.wav" -f alaw -ar 8000 -ac 1 "${VIGILIA_LISTEN_AUDIO_BASE}.alaw" >/dev/null 2>&1
ffmpeg -y -i "${VIGILIA_LISTEN_AUDIO_BASE}.wav" -f mulaw -ar 8000 -ac 1 "${VIGILIA_LISTEN_AUDIO_BASE}.ulaw" >/dev/null 2>&1
