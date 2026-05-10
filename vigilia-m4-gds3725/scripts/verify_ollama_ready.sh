#!/usr/bin/env bash
set -euo pipefail

MODEL_NAME="${VIGILIA_OLLAMA_MODEL:-llama3.2:3b}"
PROMPT="${VIGILIA_OLLAMA_TEST_PROMPT:-Responde solo OK.}"

echo "== Verificacion Ollama VIGILIA =="

if ! command -v ollama >/dev/null 2>&1; then
  echo "[FAIL] falta comando ollama"
  exit 1
fi
echo "[OK] comando ollama disponible"

if ! pgrep -x ollama >/dev/null 2>&1; then
  echo "[WARN] proceso ollama no aparece activo; probando CLI igual"
else
  echo "[OK] proceso ollama activo"
fi

if ! ollama list | awk 'NR > 1 {print $1}' | grep -qx "${MODEL_NAME}"; then
  echo "[FAIL] falta modelo ${MODEL_NAME}; corre ./scripts/bootstrap_ollama.sh"
  exit 1
fi
echo "[OK] modelo ${MODEL_NAME} disponible"

if ollama run "${MODEL_NAME}" "${PROMPT}" >/dev/null; then
  echo "[OK] modelo responde"
else
  echo "[FAIL] modelo no responde"
  exit 1
fi

echo "Ollama listo para backend conversacional."
