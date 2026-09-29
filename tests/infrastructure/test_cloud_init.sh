#!/usr/bin/env bash
set -euo pipefail

template="infra/terraform/templates/cloud-init.yaml.tftpl"

[[ -f "${template}" ]] || {
  echo "cloud-init template is required" >&2
  exit 1
}

grep -q 'amazon-ssm-agent' "${template}"
grep -q 'systemctl enable --now.*amazon-ssm-agent' "${template}"
grep -q "INSTALL_K3S_VERSION='\${k3s_version}'" "${template}"
grep -q -- '--write-kubeconfig-mode 600' "${template}"
grep -q "DESIRED_VERSION='\${helm_version}'" "${template}"
grep -q 'git' "${template}"
grep -q 'curl' "${template}"
grep -q '/var/log/cloud-init-output.log' "${template}"

node_line="$(grep -n 'kubectl get node' "${template}" | head -1 | cut -d: -f1)"
marker_line="$(grep -n '/var/lib/gameops/bootstrap-complete' "${template}" | head -1 | cut -d: -f1)"
[[ "${node_line}" -lt "${marker_line}" ]] || {
  echo "bootstrap marker must be written only after the node check" >&2
  exit 1
}
