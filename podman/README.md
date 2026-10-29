# Podman on CachyOS

Use rootless Podman where possible. With a compatible Compose provider:

    podman compose up --build -d
    podman compose ps
    podman compose logs --tail=100 api
    curl -fsS http://127.0.0.1:8080/healthz
    podman compose down

The notes-data named volume is retained when Compose is brought down without -v. The container runs as a fixed non-root UID, drops capabilities, and has a read-only root filesystem. If volume ownership is the only failure, diagnose it from logs and inspect the volume; do not solve it by running as root by default.

Optional Nginx proxy:

    podman compose --profile reverse-proxy up --build -d
    curl -fsS http://127.0.0.1:8081/healthz
