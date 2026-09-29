#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "${repo_root}/work"
archive_dir="$(mktemp -d "${repo_root}/work/k6-validation.XXXXXX")"
trap 'rm -rf "${archive_dir}"' EXIT

if command -v k6 >/dev/null 2>&1; then
  k6 inspect --env BASE_URL=http://127.0.0.1 "${repo_root}/load-test/normal.js"
  k6 inspect --env BASE_URL=http://127.0.0.1 "${repo_root}/load-test/degradation.js"
  k6 archive --env BASE_URL=http://127.0.0.1 \
    --archive-out "${archive_dir}/normal.tar" "${repo_root}/load-test/normal.js"
  k6 archive --env BASE_URL=http://127.0.0.1 \
    --archive-out "${archive_dir}/degradation.tar" \
    "${repo_root}/load-test/degradation.js"
elif command -v docker >/dev/null 2>&1; then
  docker run --rm --volume "${repo_root}:/src:ro" grafana/k6:2.3.0 \
    inspect --env BASE_URL=http://127.0.0.1 /src/load-test/normal.js
  docker run --rm --volume "${repo_root}:/src:ro" grafana/k6:2.3.0 \
    inspect --env BASE_URL=http://127.0.0.1 /src/load-test/degradation.js
  chmod 0777 "${archive_dir}"
  docker run --rm --user "$(id -u):$(id -g)" \
    --volume "${repo_root}:/src:ro" --volume "${archive_dir}:/out" \
    grafana/k6:2.3.0 archive --env BASE_URL=http://127.0.0.1 \
    --archive-out /out/normal.tar /src/load-test/normal.js
  docker run --rm --user "$(id -u):$(id -g)" \
    --volume "${repo_root}:/src:ro" --volume "${archive_dir}:/out" \
    grafana/k6:2.3.0 archive --env BASE_URL=http://127.0.0.1 \
    --archive-out /out/degradation.tar \
    /src/load-test/degradation.js
else
  echo "k6 2.3.0 or Docker is required to validate load tests" >&2
  exit 1
fi

test -s "${archive_dir}/normal.tar"
test -s "${archive_dir}/degradation.tar"
echo "k6 load-test inspection and archive validation passed"
