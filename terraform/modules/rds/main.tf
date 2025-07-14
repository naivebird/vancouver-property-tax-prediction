resource "aws_db_instance" "mlflow-backend-db" {
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "15"
  instance_class       = var.db_instance
  db_name              = var.db_name
  username             = var.db_user
  password             = var.db_password
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name = aws_db_subnet_group.rds_subnet_group.name
  skip_final_snapshot  = true
  identifier = "mlflow-backend-db"
}

resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "mlflow-db-subnet-group"
  subnet_ids = var.subnet_ids
}

resource "aws_security_group" "rds_sg" {
  name        = "mlflow-rds-sg"
  vpc_id      = var.vpc_id
  ingress {
    from_port   = 5432
    to_port     = 5432
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

output "db_endpoint" {
  value = aws_db_instance.mlflow-backend-db.endpoint
}

output "rds_security_group_id" {
  value = aws_security_group.rds_sg.id
}