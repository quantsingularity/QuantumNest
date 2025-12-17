# Terraform Modules

This directory should contain reusable Terraform modules.

## Required Modules

The following modules are referenced in main.tf but not yet implemented:

- `network` - VPC, subnets, route tables, NAT gateways
- `security` - Security groups and network ACLs
- `compute` - EKS cluster and node groups
- `database` - RDS database instances
- `storage` - ElastiCache Redis clusters

## Development Note

For local development and testing, you can:

1. Use the module stubs in this directory
2. Replace module calls with inline resources
3. Use the AWS VPC, EKS, RDS modules from Terraform Registry

Example:

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  # ... configuration
}
```
