#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/vigilia_env.sh"

"$SCRIPT_DIR/prepare_repo_runtime.sh"

ASTERISK_BIN="${ASTERISK_BIN:-/usr/local/asterisk/sbin/asterisk}"
ASTERISK_CONFIG="$VIGILIA_ASTERISK_ETC_DIR/asterisk.conf"

exec "$ASTERISK_BIN" -C "$ASTERISK_CONFIG" -cvvv
