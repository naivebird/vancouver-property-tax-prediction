variable "ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for the EC2 instance"
  type        = string
}

variable "key_name" {
  description = "Key pair name for SSH access"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for the EC2 instance"
  type        = string
}

variable "mlflow_uri" {
  description = "MLflow tracking URI"
  type        = string
}

variable "docker_image" {
  description = "Docker image to run"
  type        = string
}

variable "container_port" {
  description = "Port the container exposes"
  type        = number
}

variable "user_data_tpl" {
  description = "User data template file name"
  type        = string
}

variable "s3_bucket" {
  description = "S3 bucket name for storing models"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID for ECR repository"
  type        = string
}
variable "aws_region" {
  description = "AWS region"
  type        = string
}