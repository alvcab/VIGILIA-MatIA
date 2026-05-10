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
CALL_WAIT_SECONDS="${VIGILIA_GDS_CALL_WAIT_SECONDS:-45}"
AFTER_CAPTURE_SECONDS="${VIGILIA_GDS_AFTER_CAPTURE_SECONDS:-3}"

export VIGILIA_HELLO_SIP_DOMAIN="${VIGILIA_HELLO_SIP_DOMAIN:-192.168.100.234}"
export VIGILIA_HELLO_TEXT="${VIGILIA_HELLO_TEXT:-Hola Alvaro, soy MatIA. Te escucho.}"

LISTEN_URI="$("${PYTHON_BIN}" -m app.main --mode gds-hello-test | "${PYTHON_BIN}" -c 'import json, sys; print(json.load(sys.stdin)["listen_uri"])')"
rm -f "${CAPTURED_AUDIO}"

echo "MatIA escuchando en ${LISTEN_URI}. Aprieta el boton del timbre."
echo "Cuando llegue audio, se cortara la llamada despues de ${AFTER_CAPTURE_SECONDS}s y se abrira si la decision autoriza."

cleanup() {
  if [[ -n "${BARESIP_PID:-}" ]] && kill -0 "${BARESIP_PID}" 2>/dev/null; then
    kill -INT "${BARESIP_PID}" 2>/dev/null || true
    wait "${BARESIP_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

"${BARESIP_BINARY}" -s -f "${BARESIP_CONFIG_DIR}" &
BARESIP_PID="$!"

elapsed=0
while [[ "${elapsed}" -lt "${CALL_WAIT_SECONDS}" ]]; do
  if [[ -s "${CAPTURED_AUDIO}" ]]; then
    sleep "${AFTER_CAPTURE_SECONDS}"
    cleanup
    trap - EXIT
    break
  fi
  if ! kill -0 "${BARESIP_PID}" 2>/dev/null; then
    wait "${BARESIP_PID}" 2>/dev/null || true
    break
  fi
  sleep 1
  elapsed=$((elapsed + 1))
done

if [[ -n "${BARESIP_PID:-}" ]] && kill -0 "${BARESIP_PID}" 2>/dev/null; then
  cleanup
  trap - EXIT
fi

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
