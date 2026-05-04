#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/vigilia_env.sh"

LOG_PATH="${1:-$VIGILIA_ASTERISK_LOG_PATH}"
PROMPT_WAV="${VIGILIA_PROMPT_AUDIO_BASE}.wav"
HELLO_TEXT="${VIGILIA_VTO_LOCAL_HELLO_TEXT:-Hola. Te escucho.}"

mkdir -p "$(dirname "$LOG_PATH")"

{
  echo "[LOCAL_HELLO] $(date '+%Y-%m-%d %H:%M:%S') starting"

  if [[ -f "$PROMPT_WAV" ]]; then
    nohup afplay "$PROMPT_WAV" >/dev/null 2>&1 &
    echo "[LOCAL_HELLO] source=prompt_wav path=$PROMPT_WAV"
    exit 0
  fi

  nohup say -v Monica "$HELLO_TEXT" >/dev/null 2>&1 &
  echo "[LOCAL_HELLO] source=say text=$HELLO_TEXT"
} >> "$LOG_PATH" 2>&1
