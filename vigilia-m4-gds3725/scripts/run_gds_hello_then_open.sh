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
LOCAL_TMP_DIR="${REPO_ROOT}/runtime/tmp"
CALL_WAIT_SECONDS="${VIGILIA_GDS_CALL_WAIT_SECONDS:-45}"
AFTER_CAPTURE_SECONDS="${VIGILIA_GDS_AFTER_CAPTURE_SECONDS:-3}"
HANGUP_AFTER_OPEN_SECONDS="${VIGILIA_GDS_HANGUP_AFTER_OPEN_SECONDS:-2}"
KEEP_CALL_AFTER_FAILED_OPEN_SECONDS="${VIGILIA_GDS_KEEP_CALL_AFTER_FAILED_OPEN_SECONDS:-20}"

export VIGILIA_HELLO_SIP_DOMAIN="${VIGILIA_HELLO_SIP_DOMAIN:-192.168.100.234}"
export VIGILIA_HELLO_VOICE="${VIGILIA_HELLO_VOICE:-Rocko (Español (México))}"
export VIGILIA_HELLO_TEXT="${VIGILIA_HELLO_TEXT:-Hola Alvaro, soy MatIA. Te escucho.}"

LISTEN_URI="$("${PYTHON_BIN}" -m app.main --mode gds-hello-test | "${PYTHON_BIN}" -c 'import json, sys; print(json.load(sys.stdin)["listen_uri"])')"
mkdir -p "${LOCAL_TMP_DIR}"
rm -f "${CAPTURED_AUDIO}"

echo "MatIA escuchando en ${LISTEN_URI}. Aprieta el boton del timbre."
echo "Cuando llegue audio, se abrira despues de ${AFTER_CAPTURE_SECONDS}s y luego se colgara la llamada."

cleanup() {
  if [[ -n "${BARESIP_PID:-}" ]] && kill -0 "${BARESIP_PID}" 2>/dev/null; then
    kill -INT "${BARESIP_PID}" 2>/dev/null || true
    wait "${BARESIP_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

"${BARESIP_BINARY}" -s -f "${BARESIP_CONFIG_DIR}" &
BARESIP_PID="$!"
OPEN_ATTEMPTED=0
OPENED=0

attempt_open() {
  local output_file
  output_file="$(mktemp "${LOCAL_TMP_DIR}/vigilia-gds-open.XXXXXX")"
  if "${REPO_ROOT}/scripts/process_gds_capture_and_open.sh" \
    --face-trusted \
    --face-resident-id "${VIGILIA_GDS_TEST_FACE_RESIDENT_ID:-alvaro}" \
    --face-display-name "${VIGILIA_GDS_TEST_FACE_DISPLAY_NAME:-Alvaro}" \
    --face-confidence "${VIGILIA_GDS_TEST_FACE_CONFIDENCE:-high}" \
    "$@" | tee "${output_file}"; then
    if grep -q '"opened": true' "${output_file}"; then
      OPENED=1
    fi
  else
    echo "La apertura HTTP fallo; se mantiene la llamada por ${KEEP_CALL_AFTER_FAILED_OPEN_SECONDS}s." >&2
  fi
  rm -f "${output_file}"
}

elapsed=0
while [[ "${elapsed}" -lt "${CALL_WAIT_SECONDS}" ]]; do
  if [[ -s "${CAPTURED_AUDIO}" ]]; then
    sleep "${AFTER_CAPTURE_SECONDS}"
    attempt_open "$@"
    OPEN_ATTEMPTED=1
    if [[ "${OPENED}" -eq 1 ]]; then
      sleep "${HANGUP_AFTER_OPEN_SECONDS}"
      cleanup
      trap - EXIT
    else
      sleep "${KEEP_CALL_AFTER_FAILED_OPEN_SECONDS}"
    fi
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

if [[ "${OPEN_ATTEMPTED}" -eq 0 ]]; then
  attempt_open "$@"
fi
