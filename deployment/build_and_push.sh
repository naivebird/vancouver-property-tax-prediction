#!/bin/bash
# Usage: ./build_and_push.sh <aws_region> <aws_account_id> <repository_name> <tag>

set -e

AWS_REGION=$1
AWS_ACCOUNT_ID=$2
REPO_NAME=$3
TAG=$4

if [[ -z "$AWS_REGION" || -z "$AWS_ACCOUNT_ID" || -z "$REPO_NAME" || -z "$TAG" ]]; then
  echo "Usage: $0 <aws_region> <aws_account_id> <repository_name> <tag>"
  exit 1
fi

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}:${TAG}"

# Check if the ECR repository exists, create if not
if ! aws ecr describe-repositories --repository-names "$REPO_NAME" --region "$AWS_REGION" --no-cli-pager > /dev/null 2>&1; then
  echo "ECR repository $REPO_NAME does not exist. Creating..."
  aws ecr create-repository --repository-name "$REPO_NAME" --region "$AWS_REGION" --no-cli-pager
else
  echo "ECR repository $REPO_NAME already exists."
fi

# Authenticate Docker to ECR
aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

# Build the Docker image
docker build --platform=linux/amd64 --provenance false -t "${REPO_NAME}:${TAG}" .

# Tag the image for ECR
docker tag "${REPO_NAME}:${TAG}" "$ECR_URI"

# Push the image to ECR
docker push "$ECR_URI"

echo "Docker image pushed: $ECR_URI"