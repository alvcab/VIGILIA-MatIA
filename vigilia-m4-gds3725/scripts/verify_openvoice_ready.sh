#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OPENVOICE_DIR="${VIGILIA_OPENVOICE_DIR:-${REPO_ROOT}/vendor/OpenVoice}"
OPENVOICE_VENV="${VIGILIA_OPENVOICE_VENV:-${REPO_ROOT}/.venv-openvoice}"
FAILED=0
WARNED=0

ok() { echo "[OK] $1"; }
warn() { WARNED=1; echo "[WARN] $1"; }
fail() { FAILED=1; echo "[FAIL] $1"; }

echo "== Verificacion OpenVoice VIGILIA =="

[[ -d "${OPENVOICE_DIR}/.git" ]] && ok "repo OpenVoice clonado" || fail "falta repo OpenVoice en ${OPENVOICE_DIR}"
[[ -x "${OPENVOICE_VENV}/bin/python" ]] && ok "venv OpenVoice disponible" || fail "falta venv OpenVoice en ${OPENVOICE_VENV}"

if [[ -x "${OPENVOICE_VENV}/bin/python" ]]; then
  if "${OPENVOICE_VENV}/bin/python" - <<'PY' >/dev/null 2>&1
import importlib
importlib.import_module("openvoice")
PY
  then
    ok "paquete openvoice importable"
  else
    fail "paquete openvoice no importa"
  fi
fi

if [[ -d "${OPENVOICE_DIR}/checkpoints_v2" ]]; then
  ok "checkpoints_v2 presentes"
else
  warn "faltan checkpoints_v2; descarga checkpoints oficiales antes de generar voz"
fi

if [[ -f runtime/voice/matia-reference.wav ]]; then
  ok "muestra de voz MatIA disponible"
else
  warn "falta runtime/voice/matia-reference.wav; corre ./scripts/record_matia_voice_sample.sh"
fi

if [[ "${FAILED}" -ne 0 ]]; then
  echo "OpenVoice no esta listo. Corrige los [FAIL]."
  exit 1
fi

if [[ "${WARNED}" -ne 0 ]]; then
  echo "OpenVoice base listo, con pendientes."
  exit 0
fi

echo "OpenVoice listo."
