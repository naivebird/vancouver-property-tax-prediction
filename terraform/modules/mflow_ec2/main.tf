resource "aws_iam_role" "ec2_role" {
  name = "mlflow-ec2-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "mlflow-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

resource "aws_iam_role_policy_attachment" "s3_attach" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_instance" "mlflow-server" {
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = var.subnet_id
  key_name      = var.key_name
  vpc_security_group_ids = [aws_security_group.mlflow_sg.id]
  user_data = templatefile("${path.module}/mlflow_user_data.sh.tpl", {
    rds_endpoint = var.rds_endpoint,
    s3_bucket    = var.s3_bucket,
    db_name      = var.db_name,
    db_user      = var.db_user,
    db_password = var.db_password,
  })
  tags = {
    Name = "mlflow-server"
  }
}

resource "aws_security_group" "mlflow_sg" {
  name   = "mlflow-ec2-sg"
  vpc_id = var.vpc_id
  ingress {
    from_port   = 5000
    to_port     = 5000
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
resource "aws_security_group_rule" "rds_ingress" {
  type                       = "ingress"
  from_port                  = 5432
  to_port                    = 5432
  protocol                   = "tcp"
  security_group_id          = var.rds_security_group_id
  source_security_group_id   = aws_security_group.mlflow_sg.id
}
output "mlflow_uri" {
  value = "http://${aws_instance.mlflow-server.public_dns}:5000"
}