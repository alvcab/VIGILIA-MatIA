#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/vigilia_env.sh"

ASTERISK_BIN="${ASTERISK_BIN:-/usr/local/asterisk/sbin/asterisk}"
ASTERISK_CONFIG="$VIGILIA_ASTERISK_ETC_DIR/asterisk.conf"

if [[ $# -eq 0 ]]; then
  echo "Uso: ./scripts/asterisk_repo_cli.sh \"dialplan reload\""
  exit 1
fi

exec "$ASTERISK_BIN" -C "$ASTERISK_CONFIG" -rx "$*"
