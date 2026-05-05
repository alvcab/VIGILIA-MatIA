#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_DIR/scripts/vigilia_env.sh"
FACE_ENV_PYTHON="$HOME/miniforge3/envs/vigilia-face/bin/python"

FLAG_PATH="${1:-}"
LOG_PATH="${2:-$VIGILIA_ASTERISK_LOG_PATH}"
RESPONSE_AUDIO_PATH="${3:-$VIGILIA_DEFAULT_RESPONSE_AUDIO_PATH}"
_HELLO_FLAG_PATH="${4:-}"
DONE_FLAG_PATH="${5:-}"

if [[ -z "$FLAG_PATH" ]]; then
  exit 1
fi

mkdir -p "$(dirname "$FLAG_PATH")" "$(dirname "$LOG_PATH")"
rm -f "$FLAG_PATH"
if [[ -n "$DONE_FLAG_PATH" ]]; then
  mkdir -p "$(dirname "$DONE_FLAG_PATH")"
  rm -f "$DONE_FLAG_PATH"
fi

{
  echo "[FAST_FACE] $(date '+%Y-%m-%d %H:%M:%S') starting"
  if [[ ! -x "$FACE_ENV_PYTHON" ]]; then
    echo "[FAST_FACE] python env missing: $FACE_ENV_PYTHON"
    exit 1
  fi

  "$PROJECT_DIR/scripts/play_vto_local_hello.sh" "$LOG_PATH" "$_HELLO_FLAG_PATH" || true
  export VIGILIA_DISABLE_INFERENCE_SERVICE=1
  export VIGILIA_FAST_FACE_ENTRY_ATTEMPTS=1
  export VIGILIA_FAST_FACE_ENTRY_PAUSE_SECONDS=0
  export VIGILIA_VTO_SNAPSHOT_TIMEOUT_SECONDS=0.7
  export VIGILIA_FACE_SERVICE_TIMEOUT_SECONDS=0.5
  export VIGILIA_DISABLE_VTO_SNAPSHOT=0
  export VIGILIA_ENABLE_LOCAL_FOLLOWUP_CAPTURE=0
  export VIGILIA_PLAY_RESPONSE_LOCALLY=0

  if "$FACE_ENV_PYTHON" "$PROJECT_DIR/v1/puente_vigilia.py" --fast-face-entry "$RESPONSE_AUDIO_PATH"; then
    touch "$FLAG_PATH"
    echo "[FAST_FACE] opened=1"
  else
    echo "[FAST_FACE] opened=0"
  fi
  if [[ -n "$DONE_FLAG_PATH" ]]; then
    touch "$DONE_FLAG_PATH"
  fi
} >> "$LOG_PATH" 2>&1
