# Case study: ECS Bedrock microservice

**Portfolio status:** Application, container, Terraform, tests, and CI code published; deployment rollback untested.

## Business problem

Model a containerized document-analysis service with a reproducible AWS deployment and a security scan in CI. This is a portfolio application, not a production service or measured performance claim.

## Architecture and technologies

The [FastAPI application](app/main.py) calls Bedrock through an ECS task role. The [Dockerfile](Dockerfile) builds a non-root runtime image. [Terraform](terraform/main.tf) defines ECR, ECS Fargate, IAM roles, a log group, and a security group. [GitHub Actions](.github/workflows/devsecops.yml) runs lint, tests, and image scanning on every push and pull request; it never touches AWS. A separate [manual, approval-gated workflow](.github/workflows/deploy-production.yml) pushes the image to ECR.

## What is implemented

The code includes a health endpoint, API tests, and an image scan. Pushing to `main` only validates the code — it does not push an image or touch AWS. Pushing an image to ECR requires a manual `workflow_dispatch` run of `deploy-production.yml` and approval on the protected `production` environment; that workflow still does not update the ECS service to a new task definition or roll back a failed release. Trivy is advisory (`exit-code: "0"`) in both workflows.

## Failure modes and runbooks

The [handbook failure map](https://github.com/TreyWright360/aws-cloud-operations-handbook/blob/main/architecture/master-failure-map.md) covers bad releases and missing alarms. A recorded ECS rollback runbook remains planned in the [content index](https://github.com/TreyWright360/aws-cloud-operations-handbook/blob/main/CONTENT-INDEX.md).

## Test evidence and video

**DOCUMENTATION ONLY** for AWS deployment recovery. Unit tests run in CI, but no dated failed release, rollback, restored request, latency benchmark, or video is checked in.

## Security and cost controls

The container runs as a non-root user and the task uses IAM rather than static AWS keys. The Bedrock policy currently uses `Resource = "*"`; the ECS service has a public IP and allows port 8000 from any address. `desired_count = 1` means the task costs money while deployed.

## Production improvements

Put the service behind an ALB with TLS and restricted ingress, scope the Bedrock policy, enable a blocking vulnerability gate, deploy immutable image tags through an explicit ECS update, implement rollback, and capture smoke-test and cost evidence.
