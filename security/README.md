# Security controls and scan evidence

## Initial controls

- No runtime third-party Python dependencies.
- Request bodies are capped at 16 KiB; note text is capped at 500 characters.
- Structured JSON errors, no-cache headers and X-Content-Type-Options: nosniff.
- Container uses a non-root UID, dropped capabilities, read-only root filesystem and no-new-privileges in Compose.
- Host ports are loopback-bound by default; no credentials or tokens are required.
- GitHub Actions use read-only repository permissions for CI and scanning.

## Scanner output policy

.github/workflows/security.yml runs Trivy against files/configuration and the built image. Review findings against the exact commit and note scanner version, severity, affected component, triage decision and remediation. security/reports/ is reserved for reviewed summaries or SARIF exports that are safe to publish.

There are intentionally no sample results in this directory: an empty folder is not proof of a clean scan. Never commit access tokens, .env contents, personal data or logs with secrets.

## Known non-goals

The API has no authentication, authorization, rate limiting, TLS termination or multi-tenant isolation. It should remain loopback-only. These are explicit limits of the demo, not controls that scanners can prove absent or present.
