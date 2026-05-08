#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "uso: $0 <session_id> <archivo.wav>" >&2
  exit 1
fi

SESSION_ID="$1"
SOURCE_WAV="$2"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [ ! -f "${SOURCE_WAV}" ]; then
  echo "archivo no encontrado: ${SOURCE_WAV}" >&2
  exit 1
fi

cd "${REPO_ROOT}"
python3 -m app.main --mode department-call-service-deposit-reply-audio --session-id "${SESSION_ID}" --audio-file "${SOURCE_WAV}"
