#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <image_ref>" >&2
  exit 2
fi

image_ref="$1"
[[ "${image_ref}" =~ ^[^[:space:]@]+:[0-9a-f]{40}$ ]] || {
  echo "image_ref must end with a full 40-character Git SHA tag" >&2
  exit 2
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
render_dir="$(mktemp -d)"
trap 'rm -rf "${render_dir}"' EXIT

cp -R "${repo_root}/k8s/base" "${render_dir}/base"
image_repository="${image_ref%:*}"
image_tag="${image_ref##*:}"
cat >>"${render_dir}/base/kustomization.yaml" <<EOF
images:
  - name: ghcr.io/replace-me/gameops-platform-lab/game-session-api
    newName: ${image_repository}
    newTag: ${image_tag}
EOF

kubectl_command=(kubectl)
if command -v k3s >/dev/null 2>&1; then
  kubectl_command=(k3s kubectl)
fi
"${kubectl_command[@]}" kustomize "${render_dir}/base"
