# Continuous Integration

Continuous Integration(CI)은 변경을 공유 브랜치에 통합하기 전에 동일한 검증 절차를 자동 실행하는 방식이다. 이 프로젝트의 CI는 다음 경계를 검증한다.

1. Ruff가 Python 정적 오류와 포맷 차이를 찾는다.
2. pytest가 API·입력 검증·장애 주입·메트릭 계약을 실행한다.
3. Docker가 잠긴 의존성만 사용하는 비루트 이미지를 만든다.
4. Docker image를 tar로 내보내 Trivy가 수정 가능한 CRITICAL 취약점을 차단한다. 스캐너 컨테이너에는 Docker socket을 제공하지 않는다.
5. Gitleaks가 Git 기록과 현재 파일의 비밀 노출을 검사한다.
6. actionlint가 workflow 문법과 표현식을 검사한다.

CI가 성공했다는 사실은 운영 배포가 안전하다는 보장이 아니라, 정해진 품질 문턱을 동일한 환경에서 통과했다는 재현 가능한 증거다. 이후 CD는 `main`의 성공한 CI 실행에만 연결한다.

제3자 Action은 tag가 아니라 commit SHA로 고정한다. tag는 같은 이름이 다른 commit을 가리킬 수 있지만 SHA는 실행 코드를 불변으로 만든다. 사람에게 읽기 쉬운 릴리스 이름은 `version-matrix.md`와 workflow 주석에 함께 기록한다.
