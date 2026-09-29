#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 <delay_ms> <error_rate_0_to_1> <readiness_fail_true_or_false>" >&2
  exit 2
fi

delay_ms="$1"
error_rate="$2"
readiness_fail="$3"
namespace="gameops"
deployment="game-session-api"
configmap="game-session-api"

if [[ ! "${delay_ms}" =~ ^[0-9]+$ ]]; then
  echo "delay_ms must be a non-negative integer" >&2
  exit 2
fi
if [[ ! "${error_rate}" =~ ^(0([.][0-9]+)?|1([.]0+)?)$ ]]; then
  echo "error_rate must be a number from 0.0 through 1.0" >&2
  exit 2
fi
if [[ "${readiness_fail}" != "true" && "${readiness_fail}" != "false" ]]; then
  echo "readiness_fail must be true or false" >&2
  exit 2
fi

patch="$(printf '{"data":{"FAULT_DELAY_MS":"%s","FAULT_ERROR_RATE":"%s","READINESS_FAIL":"%s"}}' \
  "${delay_ms}" "${error_rate}" "${readiness_fail}")"

k3s kubectl -n "${namespace}" patch configmap "${configmap}" \
  --type merge --patch "${patch}"
k3s kubectl -n "${namespace}" rollout restart "deployment/${deployment}"
k3s kubectl -n "${namespace}" rollout status "deployment/${deployment}" --timeout=180s
k3s kubectl -n "${namespace}" get configmap "${configmap}" \
  -o jsonpath='{.data}{"\n"}'
