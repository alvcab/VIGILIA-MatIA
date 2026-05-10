#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

LOG_DIR="${VIGILIA_SERVICE_LOG_DIR:-${REPO_ROOT}/runtime/logs}"
SLEEP_SECONDS="${VIGILIA_SERVICE_RESTART_SECONDS:-2}"
RUN_ONCE="${VIGILIA_SERVICE_RUN_ONCE:-0}"

mkdir -p "${LOG_DIR}"

echo "MatIA GDS service iniciado. Logs en ${LOG_DIR}/matia-gds-service.log"

while true; do
  {
    echo "---- $(date -u '+%Y-%m-%dT%H:%M:%SZ') ciclo GDS ----"
    ./scripts/abrir_con_rostro_identificable.sh
    echo "---- $(date -u '+%Y-%m-%dT%H:%M:%SZ') ciclo terminado ----"
  } 2>&1 | tee -a "${LOG_DIR}/matia-gds-service.log"

  if [[ "${RUN_ONCE}" == "1" ]]; then
    break
  fi

  sleep "${SLEEP_SECONDS}"
done
