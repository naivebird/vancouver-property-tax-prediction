#!/bin/bash

if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <region> <repository-name> <account-id>"
  exit 1
fi

REGION="$1"
ACCOUNT_ID="$2"
REPO="$3"

IMAGE_DIGESTS=$(aws ecr list-images \
  --region "$REGION" \
  --repository-name "$REPO" \
  --query 'imageIds[*].imageDigest' \
  --output text \
  --no-cli-pager)

if [ -z "$IMAGE_DIGESTS" ]; then
  echo "No images found in repository."
  exit 0
fi

for DIGEST in $IMAGE_DIGESTS; do
  aws ecr batch-delete-image \
    --region "$REGION" \
    --repository-name "$REPO" \
    --image-ids imageDigest="$DIGEST" \
    --no-cli-pager
done

echo "All images deleted from $REPO."