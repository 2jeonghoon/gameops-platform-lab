#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <base_url>" >&2
  exit 2
fi

base_url="${1%/}"
body="$(mktemp)"
trap 'rm -f "${body}"' EXIT

expect_status() {
  local expected="$1"
  shift
  local actual
  actual="$(curl --silent --show-error --output "${body}" --write-out '%{http_code}' "$@")"
  if [[ "${actual}" != "${expected}" ]]; then
    echo "expected HTTP ${expected}, got ${actual}: $(<"${body}")" >&2
    exit 1
  fi
}

wait_for_status() {
  local expected="$1"
  local url="$2"
  local actual="000"
  local attempt
  for ((attempt = 1; attempt <= 15; attempt++)); do
    actual="$(curl --silent --output "${body}" --write-out '%{http_code}' "${url}" || true)"
    if [[ "${actual}" == "${expected}" ]]; then
      return 0
    fi
    sleep 2
  done
  echo "expected HTTP ${expected}, got ${actual}: $(<"${body}")" >&2
  exit 1
}

wait_for_status 200 "${base_url}/healthz"
grep --quiet '"status":"ok"' "${body}"

wait_for_status 200 "${base_url}/readyz"
grep --quiet '"status":"ready"' "${body}"

expect_status 201 \
  --header 'Content-Type: application/json' \
  --data '{"region":"ap-northeast-2","player_count":16}' \
  "${base_url}/sessions"

session_id="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["id"])' "${body}")"

expect_status 200 "${base_url}/sessions/${session_id}"
python3 -c 'import json,sys; data=json.load(open(sys.argv[1])); assert data["region"]=="ap-northeast-2" and data["player_count"]==16' "${body}"

expect_status 204 --request DELETE "${base_url}/sessions/${session_id}"
[[ ! -s "${body}" ]]

echo "smoke test passed for ${base_url}"
