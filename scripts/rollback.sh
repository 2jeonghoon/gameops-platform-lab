#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <namespace> <deployment>" >&2
  exit 2
fi

namespace="$1"
deployment="$2"
base_url="${BASE_URL:-http://127.0.0.1}"

k3s kubectl -n "${namespace}" rollout undo "deployment/${deployment}"
k3s kubectl -n "${namespace}" rollout status "deployment/${deployment}" --timeout=180s
bash "$(dirname "$0")/smoke_test.sh" "${base_url}"
