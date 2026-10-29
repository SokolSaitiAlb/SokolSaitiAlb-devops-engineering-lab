# Deferred: Kubernetes

No Kubernetes manifests or Helm chart are included in the initial milestone. The application is deliberately a single-instance JSON-file service, so a multi-replica orchestration target would not be a correct deployment architecture without changing persistence first.

Revisit Kubernetes only when there is a specific operational need and a supported persistent data layer. Define health probes, resource requests/limits, security context, secrets strategy, ingress/TLS, storage, rollout and rollback, and cluster ownership before adding manifests.
