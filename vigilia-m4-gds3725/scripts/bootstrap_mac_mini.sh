#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

PYTHON_BIN="${VIGILIA_PYTHON_BIN:-${REPO_ROOT}/.venv/bin/python}"
PIP_BIN="${VIGILIA_PIP_BIN:-${PYTHON_BIN} -m pip}"

need_command() {
  local command_name="$1"
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "Falta ${command_name}."
    return 1
  fi
}

echo "== VIGILIA Mac mini bootstrap =="

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Creado .env desde .env.example. Completa IPs y credenciales locales antes de abrir en real."
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew no esta instalado. Instala Homebrew y vuelve a correr este script."
  exit 1
fi

need_command python3

if [[ ! -x "${PYTHON_BIN}" ]]; then
  python3 -m venv .venv
fi

${PIP_BIN} install --upgrade pip
${PIP_BIN} install "pytest>=8" "openai-whisper" "numpy<2"

if ! command -v ffmpeg >/dev/null 2>&1; then
  brew install ffmpeg
fi

if ! command -v baresip >/dev/null 2>&1; then
  brew install baresip
fi

need_command ffmpeg
need_command baresip
need_command say

mkdir -p runtime/logs runtime/tmp

./scripts/prepare_baresip_runtime.sh >/dev/null
${PYTHON_BIN} -m pytest

echo "Bootstrap listo."
echo "Siguiente prueba:"
echo "  ./scripts/abrir_con_rostro_identificable.sh"
echo "Servicio local:"
echo "  ./scripts/matia_gds_service.sh"
