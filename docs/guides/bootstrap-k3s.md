# k3s bootstrap 확인

EC2 생성 후 SSM 관리 노드가 Online이 될 때까지 기다린다. SSH는 사용하지 않는다.

SSM command에서 다음을 확인한다.

```bash
cloud-init status --wait
systemctl status snap.amazon-ssm-agent.amazon-ssm-agent.service --no-pager
systemctl status k3s --no-pager
k3s kubectl get nodes -o wide
test -f /var/lib/gameops/bootstrap-complete
stat -c '%a %n' /etc/rancher/k3s/k3s.yaml
helm version
```

node가 Ready가 아니면 `/var/log/cloud-init-output.log`, `journalctl -u k3s`, disk/memory, containerd image pull 오류 순서로 확인한다. marker가 없으면 `kubectl get node` 성공 전 bootstrap이 끝나지 않은 것이다. kubeconfig mode는 600이어야 한다.
