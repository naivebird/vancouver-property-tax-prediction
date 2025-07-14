resource "aws_iam_role_policy" "api_s3_access" {
  name = "api-s3-access"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject"
        ]
        Resource = [
          "arn:aws:s3:::vancouver-property-tax-models",
          "arn:aws:s3:::vancouver-property-tax-models/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role" "ec2_role" {
  name = "ec2-ecr-s3-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role_policy.json
}

data "aws_iam_policy_document" "ec2_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "ecr_s3_attach" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "ec2-ecr-s3-profile"
  role = aws_iam_role.ec2_role.name
}

resource "aws_instance" "api-server" {
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = var.subnet_id
  key_name      = var.key_name
  vpc_security_group_ids = [aws_security_group.api_sg.id]
  user_data = templatefile("${path.module}/${var.user_data_tpl}", {
    mlflow_uri  = var.mlflow_uri,
    s3_bucket   = var.s3_bucket,
    docker_image = var.docker_image,
    container_port = var.container_port,
    aws_account_id = var.aws_account_id,
    aws_region = var.aws_region,
  })
  tags = {
    Name = "api-server"
  }
  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name
}
resource "aws_security_group" "api_sg" {
  name   = "api-ec2-sg"
  vpc_id = var.vpc_id
  ingress {
    from_port   = var.container_port
    to_port     = var.container_port
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Restrict in production!
  }
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Restrict in production!
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

output "api_url" {
  value = "http://${aws_instance.api-server.public_dns}:${var.container_port}"
}