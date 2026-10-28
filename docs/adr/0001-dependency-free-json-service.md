# ADR 0001: dependency-free service with JSON-file persistence

- **Status:** Accepted for the initial portfolio phase
- **Context:** the first milestone must be small enough to run on a developer workstation and demonstrate repeatable tests, packaging, CI, security scans and recovery without adding infrastructure for its own sake.
- **Decision:** use Python's standard-library HTTP server and a JSON file protected by a process-local lock. Run one instance only, persist state on a mounted volume, and use built-in unittest for integration checks.
- **Consequences:** no runtime package installation is required and the image surface is small. The JSON store is not suitable for multiple replicas, high write throughput, multi-process writers or strong transactional requirements. A database decision should be made only when a real use case requires it.
- **Alternatives considered:** FastAPI plus an ASGI server would provide a richer framework but adds dependencies not needed for the first endpoint set; Kubernetes and Terraform are deferred because there is no current deployment target or infrastructure to provision.
