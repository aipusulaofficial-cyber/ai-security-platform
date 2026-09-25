# Architecture

Contracts, domain logic, and infrastructure adapters are isolated. Inputs are validated, resources are bounded, and failures are explicit.

## Production trade-offs
Prefer deterministic local execution and small interfaces initially. Production should externalize shared state, add OpenTelemetry, and enforce SLO, security, and resource policies.
