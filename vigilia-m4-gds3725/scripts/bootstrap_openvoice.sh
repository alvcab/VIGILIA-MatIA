#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
OPENVOICE_DIR="${VIGILIA_OPENVOICE_DIR:-${REPO_ROOT}/vendor/OpenVoice}"
OPENVOICE_VENV="${VIGILIA_OPENVOICE_VENV:-${REPO_ROOT}/.venv-openvoice}"
PYTHON_BIN="${VIGILIA_OPENVOICE_PYTHON:-python3.9}"

cd "${REPO_ROOT}"

echo "== VIGILIA OpenVoice bootstrap =="
echo "OpenVoice en: ${OPENVOICE_DIR}"
echo "Entorno en: ${OPENVOICE_VENV}"

if ! command -v git >/dev/null 2>&1; then
  echo "Falta git."
  exit 1
fi

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Falta ${PYTHON_BIN}. OpenVoice recomienda Python 3.9."
  echo "En Mac puedes instalarlo con pyenv o Homebrew antes de volver a correr."
  exit 1
fi

if [[ ! -d "${OPENVOICE_DIR}/.git" ]]; then
  mkdir -p "$(dirname "${OPENVOICE_DIR}")"
  git clone https://github.com/myshell-ai/OpenVoice.git "${OPENVOICE_DIR}"
fi

if [[ ! -x "${OPENVOICE_VENV}/bin/python" ]]; then
  "${PYTHON_BIN}" -m venv "${OPENVOICE_VENV}"
fi

"${OPENVOICE_VENV}/bin/python" -m pip install --upgrade pip wheel setuptools
"${OPENVOICE_VENV}/bin/python" -m pip install -e "${OPENVOICE_DIR}"

cat <<'MSG'
OpenVoice base instalado.

Falta descargar checkpoints oficiales antes de sintetizar:
- V1: extraer en vendor/OpenVoice/checkpoints
- V2: extraer en vendor/OpenVoice/checkpoints_v2

Luego instala MeloTTS para V2 si usaras demo_part3:
  .venv-openvoice/bin/python -m pip install git+https://github.com/myshell-ai/MeloTTS.git
  .venv-openvoice/bin/python -m unidic download

Verifica con:
  ./scripts/verify_openvoice_ready.sh
MSG
