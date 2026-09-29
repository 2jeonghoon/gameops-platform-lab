.PHONY: test lint format-check terraform-check kubernetes-check monitoring-check verify

test:
	uv run pytest

lint:
	uv run ruff check app tests

format-check:
	uv run ruff format --check app tests

terraform-check:
	terraform -chdir=infra/terraform fmt -check -recursive
	terraform -chdir=infra/terraform validate
	terraform -chdir=infra/terraform test

kubernetes-check:
	kubectl kustomize k8s/base | kubeconform -strict -summary -ignore-missing-schemas
	uv run pytest tests/kubernetes -v

monitoring-check:
	uv run pytest tests/monitoring -v
	shellcheck scripts/install_observability.sh scripts/deploy_on_instance.sh scripts/rollback.sh

verify: lint format-check test terraform-check kubernetes-check monitoring-check
