# Production S3 Backend Configuration
# Usage: terraform init -backend-config=backend-prod.hcl

bucket         = "quantumnest-terraform-state-prod"
key            = "infrastructure/terraform.tfstate"
region         = "us-west-2"
encrypt        = true
kms_key_id     = "alias/terraform-state-key"
dynamodb_table = "quantumnest-terraform-locks"
