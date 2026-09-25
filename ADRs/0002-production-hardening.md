# ADR-0002: Production hardening
FastAPI is the service edge and OpenTelemetry is the telemetry boundary. Kubernetes/Helm define bounded deployment; Terraform owns infrastructure inputs. Trivy and CycloneDX enforce supply-chain and SBOM gates; contract/property tests protect the HTTP boundary; Locust validates baseline load.
Production externalizes secrets, state, telemetry and autoscaling.
