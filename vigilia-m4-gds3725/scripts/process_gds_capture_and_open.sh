#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export VIGILIA_TRANSCRIPTION_BACKEND="${VIGILIA_GDS_CAPTURE_TRANSCRIPTION_BACKEND:-whisper-local}"
export VIGILIA_WHISPER_MODEL="${VIGILIA_WHISPER_MODEL:-tiny}"

PYTHON_BIN="${VIGILIA_PYTHON_BIN:-${REPO_ROOT}/.venv/bin/python}"

"${PYTHON_BIN}" -m app.main --mode gds-capture-open "$@"
