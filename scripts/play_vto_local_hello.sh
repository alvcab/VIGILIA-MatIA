#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/vigilia_env.sh"

LOG_PATH="${1:-$VIGILIA_ASTERISK_LOG_PATH}"
HELLO_FLAG_PATH="${2:-}"
HELLO_TEXT="${VIGILIA_VTO_LOCAL_HELLO_TEXT:-Hola.}"
HELLO_AUDIO_PATH="${VIGILIA_HELLO_AUDIO_PATH:-$VIGILIA_AUDIO_DIR/vigilia_hello.wav}"
HELLO_PLAYBACK_RATE="${VIGILIA_HELLO_PLAYBACK_RATE:-1.3}"

mkdir -p "$(dirname "$LOG_PATH")"
if [[ -n "$HELLO_FLAG_PATH" ]]; then
  mkdir -p "$(dirname "$HELLO_FLAG_PATH")"
  if [[ -f "$HELLO_FLAG_PATH" ]]; then
    exit 0
  fi
fi

{
  echo "[LOCAL_HELLO] $(date '+%Y-%m-%d %H:%M:%S') starting"

  if [[ -n "$HELLO_FLAG_PATH" ]]; then
    touch "$HELLO_FLAG_PATH"
  fi

  if [[ -f "$HELLO_AUDIO_PATH" ]] && nohup afplay -r "$HELLO_PLAYBACK_RATE" "$HELLO_AUDIO_PATH" >/dev/null 2>&1 & then
    echo "[LOCAL_HELLO] source=local_afplay_async path=$HELLO_AUDIO_PATH rate=$HELLO_PLAYBACK_RATE"
    exit 0
  fi

  if nohup say -v Monica "$HELLO_TEXT" >/dev/null 2>&1 & then
    echo "[LOCAL_HELLO] source=local_say_async text=$HELLO_TEXT"
    exit 0
  fi

  if [[ -n "$HELLO_FLAG_PATH" ]]; then
    rm -f "$HELLO_FLAG_PATH"
  fi
  echo "[LOCAL_HELLO] playback_failed"
} >> "$LOG_PATH" 2>&1
