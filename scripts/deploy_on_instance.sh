#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 <repo_url> <commit_sha> <image_ref>" >&2
  exit 2
fi

repo_url="$1"
commit_sha="$2"
image_ref="$3"
repo_dir="/opt/gameops/repository"
namespace="gameops"
deployment="game-session-api"
evidence_dir="/var/lib/gameops/evidence"

[[ "${commit_sha}" =~ ^[0-9a-f]{40}$ ]] || {
  echo "commit_sha must be a full 40-character Git SHA" >&2
  exit 2
}
[[ "${image_ref}" == *":${commit_sha}" ]] || {
  echo "image_ref must end with the verified commit SHA" >&2
  exit 2
}

cd "${repo_dir}"
git remote set-url origin "${repo_url}"
git fetch --depth=1 origin "${commit_sha}"
git checkout --detach "${commit_sha}"

install -d -m 0755 "${evidence_dir}"
previous_image="$(k3s kubectl -n "${namespace}" get deployment "${deployment}" -o jsonpath='{.spec.template.spec.containers[?(@.name=="api")].image}' 2>/dev/null || true)"
printf '%s\n' "${previous_image}" >"${evidence_dir}/previous-image"

k3s kubectl kustomize k8s/base \
  | k3s kubectl set image --local -f - "deployment/${deployment}" "api=${image_ref}" -o yaml \
  | k3s kubectl apply -f -

if ! k3s kubectl -n "${namespace}" rollout status "deployment/${deployment}" --timeout=180s; then
  evidence_file="${evidence_dir}/rollout-${commit_sha}-$(date -u +%Y%m%dT%H%M%SZ).log"
  {
    k3s kubectl -n "${namespace}" describe deployment "${deployment}"
    k3s kubectl -n "${namespace}" get pods -o wide
    k3s kubectl -n "${namespace}" get events --sort-by=.lastTimestamp
  } >"${evidence_file}" 2>&1
  echo "rollout failed; evidence preserved at ${evidence_file}; no automatic rollback performed" >&2
  exit 1
fi

bash scripts/smoke_test.sh http://127.0.0.1
