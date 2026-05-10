#!/usr/bin/env bash
set -euo pipefail

MODEL_NAME="${VIGILIA_OLLAMA_MODEL:-llama3.2:3b}"
PROMPT="${VIGILIA_OLLAMA_TEST_PROMPT:-Responde en una frase breve: listo.}"

echo "== VIGILIA Ollama bootstrap =="

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew no esta instalado. Instala Homebrew antes de preparar Ollama."
  exit 1
fi

if ! command -v ollama >/dev/null 2>&1; then
  brew install ollama
fi

if ! pgrep -x ollama >/dev/null 2>&1; then
  echo "Iniciando servicio ollama serve en segundo plano."
  mkdir -p runtime/logs
  nohup ollama serve >runtime/logs/ollama-serve.log 2>&1 &
  sleep 3
fi

echo "Descargando/verificando modelo ${MODEL_NAME}."
ollama pull "${MODEL_NAME}"

echo "Probando modelo ${MODEL_NAME}."
ollama run "${MODEL_NAME}" "${PROMPT}"

echo "Ollama listo."
echo "Para activar backend conversacional en .env:"
echo "  VIGILIA_MODEL_BACKEND=ollama"
echo "  VIGILIA_OLLAMA_MODEL=${MODEL_NAME}"
