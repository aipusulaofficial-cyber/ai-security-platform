# Deployment verification

1. Build from the exact source revision.
2. Verify non-root execution and resource bounds.
3. Apply Kubernetes/Helm and confirm readiness.
4. Confirm representative domain smoke behavior.
5. Verify request_id/correlation_id and telemetry configuration.
6. Confirm security/SBOM checks for the same revision.
7. Record revision and rollback target.

Manifest presence is not deployment verification; these checks must execute in the target environment.