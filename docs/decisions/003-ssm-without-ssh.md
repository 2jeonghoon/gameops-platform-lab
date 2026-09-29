# ADR-003: SSH 대신 AWS Systems Manager를 사용한다

- 상태: 채택
- 날짜: 2026-09-29

공개 SSH 22와 key pair를 만들지 않는다. EC2 instance profile에 `AmazonSSMManagedInstanceCore`를 연결하고, GitHub deploy role은 제한된 SSM command만 보낸다.

공격 표면과 개인 key 관리가 줄고 명령 결과를 AWS에서 조회할 수 있다. 대신 SSM agent, IAM, outbound AWS API 연결이 모두 정상이어야 하며 장애 시 console 기반 복구가 필요할 수 있다.
