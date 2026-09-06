output "ecr_repository_url" {
  description = "Amazon ECR Repository URI for container images."
  value       = aws_ecr_repository.app.repository_url
}

output "ecs_cluster_name" {
  description = "Name of the Amazon ECS Fargate cluster."
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "Name of the running ECS Service."
  value       = aws_ecs_service.app.name
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group destination for container stdout/stderr."
  value       = aws_cloudwatch_log_group.app.name
}
