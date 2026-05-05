#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/vigilia_env.sh"

FLAG_PATH="$VIGILIA_RUNTIME_DIR/vigilia_audio_only.flag"
rm -f "$FLAG_PATH"
echo "VTO audio-only mode disabled: $FLAG_PATH"
