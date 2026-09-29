# AWS teardown 검증 runbook

## 파괴 전 증거 보존

실제 비용, Terraform output, 배포 SHA, dashboard screenshot, incident 기록이 repository 밖 안전한 위치에 보존됐는지 확인한다. local Terraform state는 민감 정보일 수 있으므로 commit하지 않는다.

## Terraform 제거

```bash
terraform -chdir=infra/terraform plan -destroy -out=destroy.tfplan
terraform -chdir=infra/terraform show destroy.tfplan
terraform -chdir=infra/terraform apply destroy.tfplan
```

plan에서 프로젝트 VPC, subnet, route, security group, EC2, EBS, IAM instance profile/role, GitHub deploy role, budget가 제거 대상인지 검토한 뒤에만 apply한다.

## 제거 확인

같은 AWS account와 `ap-northeast-2` region에서 프로젝트 tag를 조회한다.

```bash
aws resourcegroupstaggingapi get-resources \
  --region ap-northeast-2 \
  --tag-filters Key=Project,Values=gameops-platform-lab

aws ec2 describe-instances --region ap-northeast-2 \
  --filters Name=tag:Project,Values=gameops-platform-lab \
  --query 'Reservations[].Instances[?State.Name!=`terminated`].[InstanceId,State.Name]'

aws ec2 describe-volumes --region ap-northeast-2 \
  --filters Name=tag:Project,Values=gameops-platform-lab \
  --query 'Volumes[].{Id:VolumeId,State:State,Size:Size}'
```

Terraform state에서 관리 resource가 없고 위 조회에 비용 발생 resource가 없어야 한다. AWS Budget와 Cost Explorer는 지연 반영될 수 있으므로 최종 비용은 다음 날 다시 확인한다. GHCR image와 GitHub Actions artifact는 AWS 비용 resource가 아니므로 별도 보존 정책으로 관리한다.

## 예외 처리

남은 resource가 있으면 수동 삭제부터 하지 않는다. Terraform state와 실제 resource 불일치 원인을 확인하고 import 또는 명시적 대상 제거 계획을 세운다. orphan EBS volume, Elastic IP, NAT Gateway, Load Balancer가 없는지 별도 확인한다. 이 프로젝트는 뒤 세 종류를 생성하지 않으므로 발견되면 project 범위를 재확인한다.
