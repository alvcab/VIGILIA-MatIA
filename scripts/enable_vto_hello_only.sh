#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/vigilia_env.sh"

touch "$VIGILIA_RUNTIME_DIR/vigilia_hello_only.flag"
echo "$VIGILIA_RUNTIME_DIR/vigilia_hello_only.flag"
