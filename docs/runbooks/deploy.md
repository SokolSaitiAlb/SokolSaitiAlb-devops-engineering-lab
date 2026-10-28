# Runbook: deploy and verify

## Container deployment (local lab)

1. Confirm the intended engine is installed and the current directory is the repository root.
2. Run docker compose up --build -d or podman compose up --build -d.
3. Inspect compose ps and service logs.
4. Run ./monitoring/check-health.sh http://127.0.0.1:8080.
5. Create a test note and read it back from /api/notes.
6. Record the commit SHA, image build result and test results from the actual environment.

## Rollback/restart

This lab uses a local image tag. Keep the previously verified image tag before rebuilding, or use a versioned tag in a real deployment. A normal compose down does not remove the named data volume; avoid down -v unless you explicitly intend to destroy local lab data.

## Diagnosing a failure

    docker compose ps
    docker compose logs --tail=100 api
    docker compose logs --tail=100 nginx
    curl -v --max-time 3 http://127.0.0.1:8080/healthz

Replace docker compose with podman compose when using Podman. Capture sanitized output and the exact commit before modifying configuration.
