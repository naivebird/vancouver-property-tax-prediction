resource "aws_s3_bucket" "model_bucket" {
  bucket = var.bucket_name
  force_destroy = true
}
output "name" {
  value = aws_s3_bucket.model_bucket.bucket
}