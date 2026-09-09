# 09 - Non-functional requirements

## Scale

- **Sources / tables / total volume today:**
- **Growth rate:**
- **Peak load characteristics:**

## Performance

- **End-to-end latency target:** source change -> visible in target
- **Per-pipeline runtime budget:**

## Cost

- **Budget for compute + storage:**
- **Cost controls required:** (auto-suspend, slot limits, partition pruning)

## Environments

- **Environments:** dev / test / prod - separate projects/accounts?
- **Promotion flow:** how code and config move dev -> test -> prod
- **Test data:** synthetic / masked prod / subset

## CI/CD

- **On every change:** config validation / unit tests / integration tests
- **Deployment mechanism:** (GitHub Actions, GitLab CI, Cloud Build, manual)
- **Merge gate:** what must pass before merge

## Observability

- **Logs:** format, destination, retention
- **Metrics:** rows, bytes, duration, reject rate, freshness lag, cost
- **Dashboards:** what "healthy" looks like at a glance
- **Definition of a healthy pipeline:**

## Resilience

- **RPO / RTO:**
- **Platform outage for a day - expected behaviour and recovery:**
- **State store durability / backup:**

## Tech constraints

- Approved services only? on-prem components? network isolation / private links?
