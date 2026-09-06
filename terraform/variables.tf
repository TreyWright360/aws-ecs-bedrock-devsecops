variable "aws_region" {
  description = "AWS deployment region."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Base name for project resources."
  type        = string
  default     = "bedrock-microservice"
}

variable "environment" {
  description = "Deployment environment tier."
  type        = string
  default     = "dev"
}

variable "container_port" {
  description = "Port exposed by the Docker container."
  type        = number
  default     = 8000
}

variable "container_cpu" {
  description = "Fargate CPU allocation units (256 = 0.25 vCPU)."
  type        = number
  default     = 256
}

variable "container_memory" {
  description = "Fargate memory allocation in MB."
  type        = number
  default     = 512
}
