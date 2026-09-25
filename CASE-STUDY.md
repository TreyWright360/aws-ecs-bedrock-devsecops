# Case study: ECS Bedrock microservice

**Portfolio status:** TESTED. Deployed live to AWS twice (2026-09-23 and 2026-09-24), each time torn down clean afterward and verified. `/health` is genuinely live. A real Bedrock model-access gap was found, documented, and then made visible in the health payload itself (not fixed — it's an AWS account-level form, outside what code or Terraform can do). A bad-release lab first confirmed no circuit breaker existed; a `deployment_circuit_breaker` was then added to Terraform and re-tested — ECS rolled back the broken release automatically, no manual fix required, in 4m14s with zero user-facing downtime. The vulnerability gate is now blocking (verified clean first, then flipped from advisory). A latency benchmark is checked in. One gap remains open by design, not oversight: CI still doesn't run `terraform apply` or update the ECS service — see "What is implemented" below.

## Business problem

Model a containerized document-analysis service with a reproducible AWS deployment and a security scan in CI. This is a portfolio application, not a production service or measured performance claim.

## Architecture and technologies

The [FastAPI application](app/main.py) calls Bedrock through an ECS task role. The [Dockerfile](Dockerfile) builds a non-root runtime image. [Terraform](terraform/main.tf) defines ECR, ECS Fargate, IAM roles, a log group, and a security group. [GitHub Actions](.github/workflows/devsecops.yml) runs lint, tests, and image scanning on every push and pull request; it never touches AWS. A separate [manual, approval-gated workflow](.github/workflows/deploy-production.yml) pushes the image to ECR.

## What is implemented

The code includes a health endpoint, API tests, and an image scan. Pushing to `main` only validates the code — it does not push an image or touch AWS. Pushing an image to ECR requires a manual `workflow_dispatch` run of `deploy-production.yml` and approval on the protected `production` environment; that workflow still does not update the ECS service to a new task definition, and **it does not apply Terraform at all** — the cluster, service, task definition, IAM roles, and security group were applied directly, outside CI, since no workflow does it. What CI *does* enforce as of 2026-09-24: Trivy is a **blocking** gate (`exit-code: "1"`), verified clean against the current image before the gate was flipped, not assumed clean. Rollback on a bad release is now handled at the ECS layer (`deployment_circuit_breaker`), independent of whichever pipeline pushed the image.

## Failure modes and runbooks

The [handbook failure map](https://github.com/TreyWright360/aws-cloud-operations-handbook/blob/main/architecture/master-failure-map.md) covers bad releases and missing alarms. A recorded ECS rollback runbook remains planned in the [content index](https://github.com/TreyWright360/aws-cloud-operations-handbook/blob/main/CONTENT-INDEX.md).

## Test evidence and video

**TESTED**, across two dated rounds. [Full evidence](https://github.com/TreyWright360/aws-cloud-operations-handbook/blob/main/evidence/ecs-bedrock-deployment/INDEX.md) covers: a live `/health` check; a genuine (not staged) Bedrock `Converse` denial — this account hasn't submitted Anthropic's use-case-details form, so `/api/analyze` silently returns `HTTP 200` with canned text instead of a real model response, and that gap is now surfaced in `/health`'s own `bedrock.reachable` field; a first bad-release lab that confirmed an unbounded ECS retry loop with no circuit breaker (zero user-facing downtime, but wasted compute); a second bad-release lab, after adding `deployment_circuit_breaker`, where ECS rolled back the same failure automatically in 4m14s with no manual step; a Trivy scan run in blocking mode against the real image (0 CRITICAL/HIGH) before the CI gate was made blocking; and a 20-request latency benchmark against the live task (`/health` avg 1179.5ms, `/api/analyze` avg 1268.0ms, measured client-side — not a load-test-grade number, noted as a limit). No video is checked in yet.

## Security and cost controls

The container runs as a non-root user and the task uses IAM rather than static AWS keys. The Bedrock policy currently uses `Resource = "*"`; the ECS service has a public IP and allows port 8000 from any address. `desired_count = 1` means the task costs money while deployed.

## Production improvements

**Closed, confirmed by lab (2026-09-24):** `deployment_circuit_breaker` with rollback on the ECS service — re-tested, auto-rollback in 4m14s with no manual step. `/health` now reports Bedrock reachability as data (`bedrock.reachable`) without gating the HTTP status on a downstream AWS dependency. The Trivy gate is blocking, not advisory, verified clean before the flip.

**Still open:** put the service behind an ALB with TLS and restricted ingress, scope the Bedrock policy down from `Resource = "*"`, wire `terraform apply` and an ECS service update into the gated deploy workflow (currently applied by hand, outside CI), deploy immutable image tags instead of floating `:latest`, and submit the Anthropic use-case-details form in the Bedrock console so `Converse` calls stop falling back silently — that one is a manual, account-holder action outside what Terraform or the CLI can do.
