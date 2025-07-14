#!/bin/bash
yum update -y
yum install -y docker aws-cli
service docker start
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin ${aws_account_id}.dkr.ecr.${aws_region}.amazonaws.com
docker pull ${docker_image}
docker run -d -p ${container_port}:8000 \
  -e MLFLOW_TRACKING_URI=${mlflow_uri} \
  ${docker_image}

  docker run -d -p 8000:8000 \
  -e MLFLOW_TRACKING_URI=http://ec2-35-90-111-52.us-west-2.compute.amazonaws.com:5000 410614794368.dkr.ecr.us-west-2.amazonaws.com/vancouver-property-tax-prediction:latest