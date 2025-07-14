variable "key_name" {
  description = "Key pair name for SSH access"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs"
  type        = list(string)
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "model_bucket" {
  description = "S3 bucket name for models"
  type        = string
}

variable "rds_db_name" {
  description = "RDS database name"
  type        = string
}

variable "rds_db_user" {
  description = "RDS database user"
  type        = string
}

variable "rds_db_password" {
  description = "RDS database password"
  type        = string
}

variable "rds_instance" {
  description = "RDS instance type"
  type        = string
}

variable "mlflow_instance_type" {
  description = "Instance type for MLflow EC2"
  type        = string
}

variable "ecr_repo_name" {
  description = "ECR repository name"
  type        = string
}

variable "ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
}

variable "repository_url" {
    description = "ECR repository URL for the Docker image"
    type        = string
}
variable "docker_image" {
    description = "Docker image to run"
    type        = string
}