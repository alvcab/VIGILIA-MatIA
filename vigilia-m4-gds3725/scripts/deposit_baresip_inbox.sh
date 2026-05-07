#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "uso: $0 <archivo.wav> <session_id> [caller_id] [device_label] [transport]" >&2
  exit 1
fi

SOURCE_WAV="$1"
SESSION_ID="$2"
CALLER_ID="${3:-gds3725-front-door}"
DEVICE_LABEL="${4:-gds3725}"
TRANSPORT="${5:-sip-udp}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKDIR="${VIGILIA_BARESIP_WORKDIR:-${REPO_ROOT}/runtime/baresip}"
INBOX_DIR="${WORKDIR}/inbox"

mkdir -p "${INBOX_DIR}"

if [ ! -f "${SOURCE_WAV}" ]; then
  echo "archivo no encontrado: ${SOURCE_WAV}" >&2
  exit 1
fi

TARGET_WAV="${INBOX_DIR}/${SESSION_ID}.wav"
TARGET_JSON="${INBOX_DIR}/${SESSION_ID}.json"
TEMP_WAV="${TARGET_WAV}.tmp"
TEMP_JSON="${TARGET_JSON}.tmp"

cp "${SOURCE_WAV}" "${TEMP_WAV}"

cat > "${TEMP_JSON}" <<EOF
{
  "session_id": "${SESSION_ID}",
  "caller_id": "${CALLER_ID}",
  "device_label": "${DEVICE_LABEL}",
  "transport": "${TRANSPORT}",
  "received_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF

# El watcher busca archivos .wav finales, asi que el audio definitivo debe ser la ultima senal.
mv "${TEMP_JSON}" "${TARGET_JSON}"
mv "${TEMP_WAV}" "${TARGET_WAV}"

echo "inbox_wav=${TARGET_WAV}"
echo "inbox_json=${TARGET_JSON}"
