#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

PYTHON_BIN="${VIGILIA_PYTHON_BIN:-${REPO_ROOT}/.venv/bin/python}"
FAILED=0
WARNED=0

mark_ok() {
  echo "[OK] $1"
}

mark_warn() {
  WARNED=1
  echo "[WARN] $1"
}

mark_fail() {
  FAILED=1
  echo "[FAIL] $1"
}

need_command() {
  local command_name="$1"
  if command -v "${command_name}" >/dev/null 2>&1; then
    mark_ok "comando disponible: ${command_name}"
  else
    mark_fail "falta comando: ${command_name}"
  fi
}

env_value() {
  local name="$1"
  awk -F= -v key="${name}" '$1 == key {print substr($0, index($0, "=") + 1)}' .env | tail -n 1 | sed 's/^"//; s/"$//'
}

echo "== Verificacion Mac mini VIGILIA =="

if [[ -f .env ]]; then
  mark_ok ".env existe"
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
else
  mark_fail ".env no existe; corre ./scripts/bootstrap_mac_mini.sh primero"
fi

if [[ -x "${PYTHON_BIN}" ]]; then
  mark_ok "venv python disponible: ${PYTHON_BIN}"
else
  mark_fail "no existe ${PYTHON_BIN}; corre ./scripts/bootstrap_mac_mini.sh"
fi

need_command git
need_command ffmpeg
need_command baresip
need_command say

if [[ -x "${PYTHON_BIN}" ]]; then
  if "${PYTHON_BIN}" -m pytest --version >/dev/null 2>&1; then
    mark_ok "pytest disponible en .venv"
  else
    mark_fail "pytest no esta disponible en .venv"
  fi

  if "${PYTHON_BIN}" - <<'PY' >/dev/null 2>&1
import importlib
importlib.import_module("whisper")
PY
  then
    mark_ok "Whisper local disponible"
  else
    mark_warn "Whisper local no disponible; las pruebas con --face-trusted igual no lo necesitan"
  fi
fi

mkdir -p runtime/logs runtime/tmp

if ./scripts/prepare_baresip_runtime.sh >/dev/null 2>&1; then
  mark_ok "runtime de baresip generado"
else
  mark_fail "no se pudo generar runtime de baresip"
fi

for path in runtime/baresip/config runtime/baresip/accounts scripts/abrir_con_rostro_identificable.sh scripts/matia_gds_service.sh; do
  if [[ -e "${path}" ]]; then
    mark_ok "existe ${path}"
  else
    mark_fail "falta ${path}"
  fi
done

if [[ -f .env ]]; then
  local_domain="$(env_value VIGILIA_HELLO_SIP_DOMAIN)"
  sip_domain="$(env_value VIGILIA_SIP_LOCAL_DOMAIN)"
  gds_url="$(env_value VIGILIA_GDS_BASE_URL)"
  gds_user="$(env_value VIGILIA_GDS_USERNAME)"
  gds_pin="$(env_value VIGILIA_GDS_REMOTE_PIN)"
  hello_voice="$(env_value VIGILIA_HELLO_VOICE)"

  [[ -n "${sip_domain}" ]] && mark_ok "VIGILIA_SIP_LOCAL_DOMAIN=${sip_domain}" || mark_warn "falta VIGILIA_SIP_LOCAL_DOMAIN"
  if [[ -n "${local_domain}" ]]; then
    mark_ok "VIGILIA_HELLO_SIP_DOMAIN=${local_domain}"
  elif [[ -n "${sip_domain}" ]]; then
    mark_ok "VIGILIA_HELLO_SIP_DOMAIN usara fallback VIGILIA_SIP_LOCAL_DOMAIN=${sip_domain}"
  else
    mark_fail "falta VIGILIA_HELLO_SIP_DOMAIN o VIGILIA_SIP_LOCAL_DOMAIN"
  fi
  [[ -n "${hello_voice}" ]] && mark_ok "VIGILIA_HELLO_VOICE=${hello_voice}" || mark_warn "falta VIGILIA_HELLO_VOICE"

  case "${gds_url}" in
    "" )
      mark_fail "falta VIGILIA_GDS_BASE_URL"
      ;;
    "http://192.168.100.60" )
      mark_warn "VIGILIA_GDS_BASE_URL sigue con valor de ejemplo"
      ;;
    * )
      mark_ok "VIGILIA_GDS_BASE_URL configurado"
      ;;
  esac

  [[ -n "${gds_user}" ]] && mark_ok "VIGILIA_GDS_USERNAME configurado" || mark_warn "falta VIGILIA_GDS_USERNAME"
  [[ -n "${gds_pin}" ]] && mark_ok "VIGILIA_GDS_REMOTE_PIN configurado" || mark_warn "falta VIGILIA_GDS_REMOTE_PIN"
fi

if [[ -x "${PYTHON_BIN}" ]]; then
  if "${PYTHON_BIN}" -m pytest tests/test_baresip_hello_runtime.py tests/test_gds37xx_http_gate.py >/dev/null; then
    mark_ok "tests criticos GDS pasan"
  else
    mark_fail "fallaron tests criticos GDS"
  fi
fi

echo "== Resultado =="
if [[ "${FAILED}" -ne 0 ]]; then
  echo "Mac mini NO listo. Corrige los [FAIL]."
  exit 1
fi

if [[ "${WARNED}" -ne 0 ]]; then
  echo "Mac mini casi listo. Revisa los [WARN] antes de produccion."
  exit 0
fi

echo "Mac mini listo para prueba con GDS."
