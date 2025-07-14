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

variable "rds_endpoint" {
    description = "RDS database endpoint for the MLflow EC2 instance"
    type        = string
}

variable "s3_bucket" {
  description = "S3 bucket name for storing models"
  type        = string
}
variable "db_password" {
    description = "RDS database password"
    type        = string
    sensitive   = true
}

variable "rds_security_group_id" {
  description = "The security group ID of the RDS instance"
  type        = string
}
variable "db_name" {
  description = "RDS database name"
  type        = string
}
variable "db_user" {
  description = "RDS database user"
  type        = string
}