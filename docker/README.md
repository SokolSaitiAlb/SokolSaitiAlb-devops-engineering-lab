# Container image

Build from the repository root:

    docker build --pull -f docker/Dockerfile -t ops-notes-api:local .

The Dockerfile copies only the service module into a slim Python image and runs as UID/GID 10001. Compose applies a read-only root filesystem, bounded /tmp, dropped capabilities and no-new-privileges. Persistent records belong in /data, not the container writable layer.

Inspect effective image settings:

    docker image inspect ops-notes-api:local --format '{{.Config.User}} {{.Config.ExposedPorts}}'

A successful image build is not a security assessment; review the Trivy workflow output for the current commit.
