# System overview

## Request and persistence flow

    Client -> optional Nginx -> Python standard-library HTTP service
                               |
                               v
                      notes.json under /data
    Git commit -> GitHub Actions CI (compile, test, lint, image build)
    Git commit -> Trivy source/config and container scan
    Health probes -> API
    Persistent data -> backup + checksum + restore drill

## Components

- Application: app/src/service.py, no external runtime package dependencies.
- Tests: app/tests/test_service.py, integration tests that start a local HTTP server and use a temporary file.
- Packaging: docker/Dockerfile; Docker Compose and Podman Compose use the same image definition.
- Ingress: optional Nginx profile, loopback-only by default.
- Single-host alternative: systemd/ops-notes-api.service.
- Automation: CI checks compile, test, lint and image build; security automation scans source/config and image.
- Operations: health checks, backup/restore and an outage/recovery drill.

## Important boundaries

The JSON store uses a process-local thread lock and atomic file replacement. It is not a database and is not safe as a shared writable store for multiple service replicas. Use one instance only; migrate to a database with an explicit consistency and backup plan before scaling horizontally.

 /healthz tests HTTP liveness. /readyz tests basic access to the current data path; it does not execute a write test. The service binds to all interfaces inside the container, but the host-published port is loopback-bound. Nginx adds a second loopback-bound entry point, not public TLS.

No Terraform module or Kubernetes manifest is included. See the deferral notes under terraform/ and kubernetes/.
