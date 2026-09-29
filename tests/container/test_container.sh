#!/usr/bin/env bash
set -euo pipefail

image="gameops-api:test"
container="gameops-api-contract"
port="18000"

cleanup() {
  docker rm -f "${container}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

if [[ ! -f Dockerfile ]]; then
  echo "Dockerfile is required" >&2
  exit 1
fi

command -v docker >/dev/null || {
  echo "docker CLI is required" >&2
  exit 1
}

docker build --tag "${image}" .

runtime_uid="$(docker run --rm --entrypoint=id "${image}" -u)"
if [[ "${runtime_uid}" == "0" ]]; then
  echo "container must not run as root" >&2
  exit 1
fi

docker run --detach --name "${container}" --publish "${port}:8000" "${image}" >/dev/null

for _ in {1..30}; do
  health="$(docker inspect --format '{{.State.Health.Status}}' "${container}")"
  if [[ "${health}" == "healthy" ]]; then
    break
  fi
  sleep 1
done

if [[ "${health}" != "healthy" ]]; then
  docker logs "${container}" >&2
  echo "container did not become healthy" >&2
  exit 1
fi

curl --fail --silent "http://127.0.0.1:${port}/healthz" | grep --quiet '"status":"ok"'
curl --fail --silent "http://127.0.0.1:${port}/readyz" | grep --quiet '"status":"ready"'
curl --fail --silent "http://127.0.0.1:${port}/metrics" | grep --quiet 'gameops_http_requests_total'
