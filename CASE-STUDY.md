# Case study: ECS Bedrock microservice

**Portfolio status:** PARTIALLY TESTED. Deployed live to AWS on 2026-09-23. `/health` verified live and healthy. A real Bedrock model-access gap was found and documented (not a code bug). A bad-release lab confirmed no deployment circuit breaker exists, with zero user-facing downtime as the specific, measured nuance.

## Business problem

Model a containerized document-analysis service with a reproducible AWS deployment and a security scan in CI. This is a portfolio application, not a production service or measured performance claim.

## Architecture and technologies

The [FastAPI application](app/main.py) calls Bedrock through an ECS task role. The [Dockerfile](Dockerfile) builds a non-root runtime image. [Terraform](terraform/main.tf) defines ECR, ECS Fargate, IAM roles, a log group, and a security group. [GitHub Actions](.github/workflows/devsecops.yml) runs lint, tests, and image scanning on every push and pull request; it never touches AWS. A separate [manual, approval-gated workflow](.github/workflows/deploy-production.yml) pushes the image to ECR.

## What is implemented

The code includes a health endpoint, API tests, and an image scan. Pushing to `main` only validates the code — it does not push an image or touch AWS. Pushing an image to ECR requires a manual `workflow_dispatch` run of `deploy-production.yml` and approval on the protected `production` environment; that workflow still does not update the ECS service to a new task definition or roll back a failed release, and **it does not apply Terraform at all** — the cluster, service, task definition, IAM roles, and security group were applied directly, outside CI, since no workflow does it. Trivy is advisory (`exit-code: "0"`) in both workflows.

## Failure modes and runbooks

The [handbook failure map](https://github.com/TreyWright360/aws-cloud-operations-handbook/blob/main/architecture/master-failure-map.md) covers bad releases and missing alarms. A recorded ECS rollback runbook remains planned in the [content index](https://github.com/TreyWright360/aws-cloud-operations-handbook/blob/main/CONTENT-INDEX.md).

## Test evidence and video

**PARTIALLY TESTED.** [Dated evidence](https://github.com/TreyWright360/aws-cloud-operations-handbook/blob/main/evidence/ecs-bedrock-deployment/INDEX.md) covers: a live `/health` check; a genuine (not staged) Bedrock `Converse` denial — this account hasn't submitted Anthropic's use-case-details form, so `/api/analyze` silently returns `HTTP 200` with canned text instead of a real model response; and a bad-release lab that pushed a crashing image as `:latest` and confirmed an unbounded ECS retry loop with no circuit breaker, but zero user-facing downtime because the last good task was never replaced. No latency benchmark or video is checked in yet.

## Security and cost controls

The container runs as a non-root user and the task uses IAM rather than static AWS keys. The Bedrock policy currently uses `Resource = "*"`; the ECS service has a public IP and allows port 8000 from any address. `desired_count = 1` means the task costs money while deployed.

## Production improvements

Put the service behind an ALB with TLS and restricted ingress, scope the Bedrock policy, enable a blocking vulnerability gate, deploy immutable image tags through an explicit ECS update, implement rollback, and capture smoke-test and cost evidence. Confirmed by lab, not just inferred: add `deployment_circuit_breaker` with rollback to the ECS service (currently absent — a bad release retries forever instead of stopping), make `/health` also check Bedrock reachability so a model-access failure isn't invisible to monitoring, and submit the Anthropic use-case-details form in the Bedrock console so `Converse` calls stop falling back silently.
