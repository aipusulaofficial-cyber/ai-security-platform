# Failure matrix

| Failure | Detection | Action | Retry? | Impact |
|---|---|---|---|---|
| Invalid input | validation | reject | No | 4xx |
| Dependency timeout | timeout budget | normalize | Safe/idempotent only | bounded failure/degradation |
| Dependency error | adapter | exponential backoff | Safe/idempotent only | bounded latency |
| Repeated failure | circuit breaker | open circuit | No while open | fast failure |
| Overload | bounded executor/token bucket | fail fast/degrade | No | 429/degraded |
| Telemetry failure | exporter | preserve domain result | exporter-local | no corruption |

Policy dependency timeout -> fail closed; repeated failure -> circuit open; malformed policy -> reject; audit write failure must be visible and never silently grant access.