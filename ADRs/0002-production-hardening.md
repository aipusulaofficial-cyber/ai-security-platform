# ADR-0002: Production hardening and domain boundaries

## Context
The platform must demonstrate an executable domain model rather than a placeholder HTTP endpoint. The service boundary must remain observable, testable and deployable.

## Decision
The core domain is implemented as prompt threat inspection and auditable security context. FastAPI exposes the domain contract and maps expected validation failures to HTTP 400. Kubernetes and Helm provide bounded resources, probes, non-root execution, horizontal scaling and disruption protection. Terraform manages the Kubernetes Deployment and Service as infrastructure-as-code.

OpenTelemetry is configured through a dedicated module with OTLP export when configured and a local console fallback. JSON logging keeps operational records machine-readable.

CI runs unit, contract/property, production smoke and supply-chain checks. Trivy scans the filesystem and CycloneDX emits an SBOM. Locust exercises the domain HTTP surface.

## Failure modes
Invalid domain input is rejected deterministically. State-machine violations fail closed. Expired or unauthorized data is rejected. Kubernetes readiness prevents traffic before the API is serving. Durable state, secrets and telemetry are externalized in production.

## Alternatives considered
A generic CRUD/acceptance endpoint was rejected because it does not demonstrate domain invariants. Provider-specific persistence was not embedded in the reference implementation to preserve a portable architecture.

## Consequences
The repository now exposes a concrete domain core plus API and operational contracts. Production integration can replace in-memory components with durable stores and inject cloud credentials and telemetry configuration without changing the domain API.
