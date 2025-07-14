#!/bin/bash
yum update -y
yum install -y python3-pip awscli

pip3 install --user mlflow boto3 psycopg2-binary

export PATH=$PATH:~/.local/bin

export MLFLOW_S3_ENDPOINT_URL=https://s3.amazonaws.com

mlflow server \
  --backend-store-uri postgresql://${db_user}:${db_password}@${rds_endpoint}/${db_name} \
  --default-artifact-root s3://${s3_bucket}/mlflow/ \
  --host 0.0.0.0 \
  --port 5000 &