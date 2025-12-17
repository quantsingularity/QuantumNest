# Backend configuration for Terraform state
# For local development, use local backend (default)
# For production, configure S3 backend in backend-prod.hcl

# Uncomment for S3 backend (production):
# terraform {
#   backend "s3" {
#     # Configuration provided via backend-prod.hcl
#   }
# }

# Local backend is used by default for development
# State file: terraform.tfstate (git-ignored)
