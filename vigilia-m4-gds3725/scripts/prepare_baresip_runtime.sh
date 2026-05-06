#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"
python3 - <<'PY'
import json

from services.telephony.baresip_runtime import BaresipRuntimeBuilder

result = BaresipRuntimeBuilder().prepare()
print(json.dumps(result, ensure_ascii=True, indent=2))
PY
