# GitHub OIDC와 AWS 역할 위임

GitHub Actions는 각 실행에 짧은 수명의 OIDC token을 발급할 수 있다. AWS IAM은 token의 발급자, audience, subject를 확인한 뒤 임시 role credential을 반환한다. 따라서 장기 AWS access key를 GitHub secret에 저장하지 않는다.

이 프로젝트의 trust policy는 다음을 모두 만족해야 한다.

- issuer: `https://token.actions.githubusercontent.com`
- audience: `sts.amazonaws.com`
- subject: 정확한 `<owner>/<repository>`의 `main` branch

위임받은 deploy role은 instance 조회와 SSM command 전송·결과 조회만 허용한다. EC2 생성·수정·삭제나 IAM 변경 권한은 없다. `SendCommand`는 `AWS-RunShellScript` document와 `Project` tag가 맞는 instance로 제한한다.

OIDC는 credential 보관 문제를 줄이지만 workflow 자체가 권한 경계가 된다. 그래서 third-party Action을 commit SHA로 고정하고, pull request code가 deploy role을 얻지 못하도록 main subject를 고정한다.
