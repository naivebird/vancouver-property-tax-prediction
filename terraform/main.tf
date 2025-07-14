terraform {
  required_version = ">= 1.0"
  backend "s3" {
    bucket  = "tf-state-vancouver-property-tax-prediction"
    key     = "vancouver-property-tax-prediction-stg.tfstate"
    region  = "us-west-2"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

module "s3_bucket" {
  source = "./modules/s3"
  bucket_name = var.model_bucket
}

module "rds" {
  source         = "./modules/rds"
  db_name        = var.rds_db_name
  db_user        = var.rds_db_user
  db_password    = var.rds_db_password
  db_instance    = var.rds_instance
  vpc_id         = var.vpc_id
  subnet_ids     = var.subnet_ids
}
module "mlflow_ec2" {
  source                = "./modules/mflow_ec2"
  ami_id                = var.ami_id
  instance_type         = var.mlflow_instance_type
  key_name              = var.key_name
  vpc_id                = var.vpc_id
  subnet_id             = var.subnet_ids[0]
  rds_endpoint          = module.rds.db_endpoint
  s3_bucket             = module.s3_bucket.name
  db_password           = var.rds_db_password
  rds_security_group_id = module.rds.rds_security_group_id
  db_name               = var.rds_db_name
  db_user               = var.rds_db_user
}

module "api_ec2" {
  source         = "./modules/api_ec2"
  ami_id         = var.ami_id
  instance_type  = "t2.micro"
  key_name       = var.key_name
  vpc_id         = var.vpc_id
  subnet_id      = var.subnet_ids[0]
  mlflow_uri     = module.mlflow_ec2.mlflow_uri
  docker_image   = var.docker_image
  container_port = 8000
  user_data_tpl  = "api_user_data.sh.tpl"
  s3_bucket      = module.s3_bucket.name
  aws_account_id = data.aws_caller_identity.current.account_id
  aws_region     = var.aws_region
}

# module "ecr" {
#   source                = "./modules/ecr"
#   ecr_repo_name        = var.ecr_repo_name
# }

output "model_bucket" {
  value = module.s3_bucket.name
}

output "ecr_repo" {
  value = var.ecr_repo_name
}
output "mlflow_uri" {
  value = module.mlflow_ec2.mlflow_uri
}
output "rds_endpoint" {
  value = module.rds.db_endpoint
}
output "ec2_service_url" {
  value = module.api_ec2.api_url
}