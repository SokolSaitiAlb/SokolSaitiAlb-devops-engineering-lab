# GitHub Actions

- .github/workflows/ci.yml: Python compilation, standard-library integration tests, Ruff lint checks and container build.
- .github/workflows/security.yml: scheduled/on-change Trivy scans for filesystem configuration, secrets and vulnerabilities, plus the built container image.
- .github/dependabot.yml: weekly update PRs for pip tooling and GitHub Actions.

The jobs request read-only repository permissions. Review each run's logs and exact commit SHA. Scanner findings should be triaged and recorded before setting anything aside; do not commit secrets, credentials, personal data or raw logs containing sensitive values.
