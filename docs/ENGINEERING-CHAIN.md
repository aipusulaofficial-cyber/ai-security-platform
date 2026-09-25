# Principal Engineering Evidence Chain

> Architecture → ADR → Contracts → Tests → Security → Observability → CI/CD → Operational thinking

This page is the repository's evidence map. Each stage points to an artifact that can be inspected. Documentation describes intent; code and tests are the authority for implemented behavior.

| Stage | Evidence | What it demonstrates |
|---|---|---|
| Architecture | [ARCHITECTURE.md](../ARCHITECTURE.md) | Security policy boundaries, enforcement and audit context and system boundaries |
| ADR | [0002-production-hardening.md](../ADRs/0002-production-hardening.md) | Explicit design trade-offs and production boundaries |
| Contracts | [tests/test_security.py](../tests/test_security.py) | Contract-focused validation at the repository boundary |
| Tests | [tests/test_integration.py](../tests/test_integration.py) + [integration](../tests/test_integration.py) | Behavioral, boundary and integration evidence |
| Security | [security-SBOM workflow](../.github/workflows/security-sbom.yml) | Supply-chain/security checks in CI |
| Observability | [observability.py](../observability.py) | Structured telemetry and correlation surface |
| CI/CD | [CI workflow](../.github/workflows/ci.yml) + [production tests](../.github/workflows/production-tests.yml) | Automated validation and production-oriented checks |
| Operational thinking | [Kubernetes](../deploy/kubernetes.yaml) + [Helm](../deploy/helm) + [Terraform](../terraform) | Deployment, resource and infrastructure boundaries |

## Principal review path

1. **Architecture** — understand ownership and boundaries.
2. **ADR** — understand why the boundaries exist.
3. **Contracts** — inspect externally visible and domain-level invariants.
4. **Tests** — verify those invariants and failure semantics.
5. **Security** — inspect security and supply-chain controls.
6. **Observability** — inspect how failures and behavior become diagnosable.
7. **CI/CD** — verify that the evidence is continuously exercised.
8. **Operational thinking** — inspect deployment, rollback/resource and infrastructure concerns.

## Claim discipline

This map is intentionally evidence-based. It does not imply an SLO, capacity target, production certification or operational guarantee that is not explicitly implemented or documented elsewhere in the repository.
