# Minimal monitoring and health model

The first monitoring step is intentionally small: a container health check plus a command-line probe for /healthz and /readyz.

- GET /healthz: process is responding; it does not prove persisted writes work.
- GET /readyz: the JSON data file exists and the service process can read it while the parent directory remains writable.
- monitoring/check-health.sh [base-url]: probes both endpoints and exits non-zero if either request fails.

A future deployment can export metrics and logs to a monitoring stack once a concrete operational target exists. No telemetry or hosted monitoring service is required for the initial lab.
