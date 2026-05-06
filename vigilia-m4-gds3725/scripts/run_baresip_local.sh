#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"
"${REPO_ROOT}/scripts/prepare_baresip_runtime.sh" >/dev/null

BARESIP_BINARY="${VIGILIA_BARESIP_BINARY:-baresip}"
BARESIP_CONFIG_PATH="${VIGILIA_BARESIP_CONFIG_PATH:-runtime/baresip/config}"

echo "Launching ${BARESIP_BINARY} with config ${BARESIP_CONFIG_PATH}"
exec "${BARESIP_BINARY}" -f "${BARESIP_CONFIG_PATH}"
