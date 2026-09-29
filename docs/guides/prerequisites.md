# 사전 준비

- AWS CLI와 유효한 개인 AWS profile
- Terraform 1.16.4
- GitHub 공개 repository의 확정된 owner와 이름
- Budget 알림을 받을 이메일
- USD 15 실습 한도와 credit 만료일 확인

확인 명령:

```bash
aws sts get-caller-identity
aws configure get region
terraform version
git remote -v
```

출력의 account ID, credential, token은 문서나 screenshot에 남기지 않는다. repository 이름을 바꾸면 OIDC subject도 바뀌므로 apply 전에 최종 이름을 확정한다.
