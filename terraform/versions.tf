terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "trey-portfolio-tfstate-050451394862"
    key            = "ecs-bedrock/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "portfolio-tfstate-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "bedrock-microservice-devsecops"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}
