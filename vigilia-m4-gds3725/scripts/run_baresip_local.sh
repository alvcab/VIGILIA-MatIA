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
"${REPO_ROOT}/scripts/prepare_baresip_runtime.sh" >/dev/null

BARESIP_BINARY="${VIGILIA_BARESIP_BINARY:-baresip}"
BARESIP_CONFIG_DIR="${VIGILIA_BARESIP_WORKDIR:-runtime/baresip}"

echo "Launching ${BARESIP_BINARY} with config directory ${BARESIP_CONFIG_DIR}"
exec "${BARESIP_BINARY}" -s -f "${BARESIP_CONFIG_DIR}"
