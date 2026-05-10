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

PYTHON_BIN="${VIGILIA_PYTHON_BIN:-${REPO_ROOT}/.venv/bin/python}"
BARESIP_BINARY="${VIGILIA_BARESIP_BINARY:-baresip}"
BARESIP_CONFIG_DIR="${VIGILIA_HELLO_BARESIP_WORKDIR:-runtime/baresip-hello}"
CAPTURED_AUDIO="${BARESIP_CONFIG_DIR}/gds-rx.wav"

export VIGILIA_HELLO_TEXT="${VIGILIA_HELLO_TEXT:-Hola Alvaro, soy MatIA. Te escucho.}"

"${PYTHON_BIN}" -m app.main --mode gds-hello-test >/dev/null
rm -f "${CAPTURED_AUDIO}"

echo "MatIA escuchando en el GDS. Aprieta el boton del timbre."
echo "Cuando termine la llamada, se procesara la captura y se abrira si la decision autoriza."

"${BARESIP_BINARY}" -s -f "${BARESIP_CONFIG_DIR}"

if [[ ! -s "${CAPTURED_AUDIO}" ]]; then
  echo "No se encontro audio capturado en ${CAPTURED_AUDIO}" >&2
  exit 1
fi

"${REPO_ROOT}/scripts/process_gds_capture_and_open.sh" \
  --face-trusted \
  --face-resident-id "${VIGILIA_GDS_TEST_FACE_RESIDENT_ID:-alvaro}" \
  --face-display-name "${VIGILIA_GDS_TEST_FACE_DISPLAY_NAME:-Alvaro}" \
  --face-confidence "${VIGILIA_GDS_TEST_FACE_CONFIDENCE:-high}" \
  "$@"
