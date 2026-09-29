# VPC와 패킷 흐름

VPC(Virtual Private Cloud)는 AWS 계정 안에 만드는 논리적으로 격리된 네트워크다. 이 프로젝트는 `10.20.0.0/16` VPC 안에 `10.20.1.0/24` 공개 subnet 하나만 둔다.

```text
Internet
  → Internet Gateway
  → public route table (0.0.0.0/0 → IGW)
  → public subnet 10.20.1.0/24
  → security group TCP 80
  → EC2 / k3s ingress / API
```

Subnet의 `map_public_ip_on_launch`가 EC2에 공개 IPv4를 할당하고, route table의 기본 경로가 Internet Gateway를 향해야 양방향 인터넷 통신이 가능하다. 둘 중 하나라도 없으면 공개 subnet이라고 부르더라도 인터넷에서 인스턴스에 도달할 수 없다.

운영 환경이라면 private subnet, NAT 또는 VPC endpoint, 다중 Availability Zone, load balancer를 고려한다. 이 실습은 비용과 일주일 범위를 통제하기 위해 단일 공개 subnet을 사용하며 그 한계를 명시한다.
