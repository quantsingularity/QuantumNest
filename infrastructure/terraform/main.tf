# QuantumNest Financial Platform - Terraform Main Configuration
# This configuration creates a comprehensive, secure, and compliant infrastructure
# for financial services applications meeting SOX, PCI DSS, GDPR, and FINRA requirements

terraform {
  required_version = ">= 1.5.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    vault = {
      source  = "hashicorp/vault"
      version = "~> 3.20"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

}

# Provider Configurations
provider "aws" {
  region = var.aws_region

  # Security and compliance configurations
  default_tags {
    tags = {
      Environment         = var.environment
      Project            = "QuantumNest"
      Owner              = "Platform-Team"
      CostCenter         = "Technology"
      DataClassification = "Confidential"
      Compliance         = "PCI-DSS,SOX,GDPR,FINRA"
      BackupRequired     = "true"
      MonitoringEnabled  = "true"
      ManagedBy          = "Terraform"
      CreatedDate        = formatdate("YYYY-MM-DD", timestamp())
    }
  }

  # Assume role for cross-account access
  assume_role {
    role_arn     = var.assume_role_arn
    session_name = "QuantumNest-Terraform"
    external_id  = var.external_id
  }
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

provider "vault" {
  address = var.vault_address
  token   = var.vault_token
}

# Local values for common configurations
locals {
  name_prefix = "quantumnest-${var.environment}"

  # Common tags for all resources
  common_tags = {
    Environment         = var.environment
    Project            = "QuantumNest"
    Owner              = "Platform-Team"
    CostCenter         = "Technology"
    DataClassification = "Confidential"
    Compliance         = "PCI-DSS,SOX,GDPR,FINRA"
    BackupRequired     = "true"
    MonitoringEnabled  = "true"
    ManagedBy          = "Terraform"
    CreatedDate        = formatdate("YYYY-MM-DD", timestamp())
  }

  # Availability zones
  azs = slice(data.aws_availability_zones.available.names, 0, 3)

  # CIDR blocks for different environments
  vpc_cidr = var.environment == "prod" ? "10.0.0.0/16" :
             var.environment == "staging" ? "10.1.0.0/16" : "10.2.0.0/16"

  # Subnet configurations
  private_subnets = [
    cidrsubnet(local.vpc_cidr, 8, 1),
    cidrsubnet(local.vpc_cidr, 8, 2),
    cidrsubnet(local.vpc_cidr, 8, 3)
  ]

  public_subnets = [
    cidrsubnet(local.vpc_cidr, 8, 101),
    cidrsubnet(local.vpc_cidr, 8, 102),
    cidrsubnet(local.vpc_cidr, 8, 103)
  ]

  database_subnets = [
    cidrsubnet(local.vpc_cidr, 8, 201),
    cidrsubnet(local.vpc_cidr, 8, 202),
    cidrsubnet(local.vpc_cidr, 8, 203)
  ]
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# KMS Key for encryption
resource "aws_kms_key" "quantumnest_main" {
  description             = "QuantumNest main encryption key for ${var.environment}"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EnableIAMUserPermissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "AllowServiceUsage"
        Effect = "Allow"
        Principal = {
          Service = [
            "s3.amazonaws.com",
            "rds.amazonaws.com",
            "eks.amazonaws.com",
            "secretsmanager.amazonaws.com"
          ]
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-main-key"
    Type = "encryption"
  })
}

resource "aws_kms_alias" "quantumnest_main" {
  name          = "alias/${local.name_prefix}-main"
  target_key_id = aws_kms_key.quantumnest_main.key_id
}

# VPC Module
module "vpc" {
  source = "./modules/network"

  name = local.name_prefix
  cidr = local.vpc_cidr

  azs              = local.azs
  private_subnets  = local.private_subnets
  public_subnets   = local.public_subnets
  database_subnets = local.database_subnets

  enable_nat_gateway     = true
  enable_vpn_gateway     = false
  enable_dns_hostnames   = true
  enable_dns_support     = true
  enable_flow_log        = true

  # Security configurations
  enable_network_address_usage_metrics = true

  # VPC Flow Logs configuration
  flow_log_destination_type = "s3"
  flow_log_destination_arn  = aws_s3_bucket.vpc_flow_logs.arn
  flow_log_log_format      = "$${version} $${account-id} $${interface-id} $${srcaddr} $${dstaddr} $${srcport} $${dstport} $${protocol} $${packets} $${bytes} $${windowstart} $${windowend} $${action} $${flowlogstatus}"

  # Additional security groups
  manage_default_security_group = true
  default_security_group_ingress = []
  default_security_group_egress  = []

  tags = local.common_tags
}

# S3 Bucket for VPC Flow Logs
resource "aws_s3_bucket" "vpc_flow_logs" {
  bucket = "${local.name_prefix}-vpc-flow-logs"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vpc-flow-logs"
    Type = "logging"
  })
}

resource "aws_s3_bucket_encryption_configuration" "vpc_flow_logs" {
  bucket = aws_s3_bucket.vpc_flow_logs.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.quantumnest_main.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_versioning" "vpc_flow_logs" {
  bucket = aws_s3_bucket.vpc_flow_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "vpc_flow_logs" {
  bucket = aws_s3_bucket.vpc_flow_logs.id

  rule {
    id     = "flow_logs_lifecycle"
    status = "Enabled"

    expiration {
      days = 2555  # 7 years for compliance
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# Security Groups Module
module "security_groups" {
  source = "./modules/security"

  name   = local.name_prefix
  vpc_id = module.vpc.vpc_id

  # Application security groups
  create_app_sg      = true
  create_database_sg = true
  create_cache_sg    = true
  create_lb_sg       = true

  # CIDR blocks for different access levels
  private_subnets_cidr = local.private_subnets
  public_subnets_cidr  = local.public_subnets

  tags = local.common_tags
}

# EKS Cluster Module
module "eks" {
  source = "./modules/compute"

  cluster_name    = "${local.name_prefix}-cluster"
  cluster_version = var.kubernetes_version

  vpc_id                   = module.vpc.vpc_id
  subnet_ids              = module.vpc.private_subnets
  control_plane_subnet_ids = module.vpc.private_subnets

  # Security configurations
  cluster_encryption_config = [
    {
      provider_key_arn = aws_kms_key.quantumnest_main.arn
      resources        = ["secrets"]
    }
  ]

  cluster_endpoint_private_access = true
  cluster_endpoint_public_access  = true
  cluster_endpoint_public_access_cidrs = var.allowed_cidr_blocks

  # Enable logging
  cluster_enabled_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  # Node groups configuration
  node_groups = {
    application = {
      desired_capacity = 3
      max_capacity     = 20
      min_capacity     = 3

      instance_types = ["m5.xlarge", "m5.2xlarge"]
      capacity_type  = "ON_DEMAND"

      k8s_labels = {
        Environment = var.environment
        NodeType    = "application"
        SecurityZone = "restricted"
      }

      k8s_taints = [
        {
          key    = "quantumnest.com/financial-workload"
          value  = "true"
          effect = "NO_SCHEDULE"
        }
      ]
    }

    monitoring = {
      desired_capacity = 2
      max_capacity     = 5
      min_capacity     = 2

      instance_types = ["m5.large"]
      capacity_type  = "ON_DEMAND"

      k8s_labels = {
        Environment = var.environment
        NodeType    = "monitoring"
      }
    }
  }

  # IRSA (IAM Roles for Service Accounts)
  enable_irsa = true

  tags = local.common_tags
}

# RDS Database Module
module "database" {
  source = "./modules/database"

  identifier = "${local.name_prefix}-db"

  engine         = "postgres"
  engine_version = "14.9"
  instance_class = var.environment == "prod" ? "db.r5.2xlarge" : "db.r5.large"

  allocated_storage     = var.environment == "prod" ? 1000 : 100
  max_allocated_storage = var.environment == "prod" ? 5000 : 500
  storage_type         = "gp3"
  storage_encrypted    = true
  kms_key_id          = aws_kms_key.quantumnest_main.arn

  db_name  = "quantumnest"
  username = "quantumnest_admin"

  vpc_security_group_ids = [module.security_groups.database_security_group_id]
  db_subnet_group_name   = module.vpc.database_subnet_group

  # High availability and backup configurations
  multi_az               = var.environment == "prod" ? true : false
  backup_retention_period = var.environment == "prod" ? 35 : 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  # Security configurations
  deletion_protection      = var.environment == "prod" ? true : false
  skip_final_snapshot     = var.environment == "prod" ? false : true
  final_snapshot_identifier = var.environment == "prod" ? "${local.name_prefix}-final-snapshot" : null

  # Monitoring and logging
  enabled_cloudwatch_logs_exports = ["postgresql"]
  monitoring_interval            = 60
  monitoring_role_arn           = aws_iam_role.rds_enhanced_monitoring.arn
  performance_insights_enabled   = true
  performance_insights_kms_key_id = aws_kms_key.quantumnest_main.arn

  tags = merge(local.common_tags, {
    Type = "database"
    BackupSchedule = "daily"
  })
}

# RDS Enhanced Monitoring Role
resource "aws_iam_role" "rds_enhanced_monitoring" {
  name = "${local.name_prefix}-rds-enhanced-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  role       = aws_iam_role.rds_enhanced_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# ElastiCache Redis Module
module "cache" {
  source = "./modules/storage"

  cluster_id = "${local.name_prefix}-redis"

  engine         = "redis"
  engine_version = "7.0"
  node_type      = var.environment == "prod" ? "cache.r6g.xlarge" : "cache.r6g.large"

  num_cache_clusters = var.environment == "prod" ? 3 : 1

  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [module.security_groups.cache_security_group_id]

  # Security configurations
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                = random_password.redis_auth_token.result
  kms_key_id               = aws_kms_key.quantumnest_main.arn

  # Backup configurations
  snapshot_retention_limit = var.environment == "prod" ? 7 : 1
  snapshot_window         = "03:00-05:00"
  maintenance_window      = "sun:05:00-sun:07:00"

  tags = local.common_tags
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "${local.name_prefix}-redis-subnet-group"
  subnet_ids = module.vpc.private_subnets

  tags = local.common_tags
}

resource "random_password" "redis_auth_token" {
  length  = 32
  special = true
}

# Store Redis auth token in AWS Secrets Manager
resource "aws_secretsmanager_secret" "redis_auth_token" {
  name                    = "${local.name_prefix}/redis/auth-token"
  description            = "Redis authentication token for QuantumNest"
  kms_key_id            = aws_kms_key.quantumnest_main.arn
  recovery_window_in_days = 7

  tags = merge(local.common_tags, {
    Type = "secret"
  })
}

resource "aws_secretsmanager_secret_version" "redis_auth_token" {
  secret_id = aws_secretsmanager_secret.redis_auth_token.id
  secret_string = jsonencode({
    auth_token = random_password.redis_auth_token.result
  })
}


# CloudTrail for audit logging
resource "aws_cloudtrail" "quantumnest_audit" {
  name           = "${local.name_prefix}-audit-trail"
  s3_bucket_name = aws_s3_bucket.audit_logs.bucket
  s3_key_prefix  = "cloudtrail-logs"

  # Security configurations
  include_global_service_events = true
  is_multi_region_trail        = true
  enable_logging               = true
  enable_log_file_validation   = true
  kms_key_id                  = aws_kms_key.quantumnest_main.arn

  # Event selectors for comprehensive logging
  event_selector {
    read_write_type                 = "All"
    include_management_events       = true
    exclude_management_event_sources = []

    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3:::${local.name_prefix}-*/*"]
    }

    data_resource {
      type   = "AWS::S3::Bucket"
      values = ["arn:aws:s3:::${local.name_prefix}-*"]
    }
  }

  # Insight selectors for anomaly detection
  insight_selector {
    insight_type = "ApiCallRateInsight"
  }

  tags = merge(local.common_tags, {
    Type = "audit"
    Compliance = "SOX,PCI-DSS,GDPR"
  })
}

# S3 Bucket for audit logs
resource "aws_s3_bucket" "audit_logs" {
  bucket = "${local.name_prefix}-audit-logs"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-audit-logs"
    Type = "audit"
  })
}

resource "aws_s3_bucket_encryption_configuration" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.quantumnest_main.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_versioning" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id

  rule {
    id     = "audit_logs_lifecycle"
    status = "Enabled"

    # Transition to IA after 30 days
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Transition to Glacier after 90 days
    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    # Transition to Deep Archive after 1 year
    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    # Retain for 7 years for compliance
    expiration {
      days = 2555
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# CloudTrail S3 bucket policy
resource "aws_s3_bucket_policy" "audit_logs" {
  bucket = aws_s3_bucket.audit_logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSCloudTrailAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.audit_logs.arn
      },
      {
        Sid    = "AWSCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.audit_logs.arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })
}

# Config for compliance monitoring
resource "aws_config_configuration_recorder" "quantumnest_config" {
  name     = "${local.name_prefix}-config-recorder"
  role_arn = aws_iam_role.config.arn

  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

resource "aws_config_delivery_channel" "quantumnest_config" {
  name           = "${local.name_prefix}-config-delivery"
  s3_bucket_name = aws_s3_bucket.config_logs.bucket
  s3_key_prefix  = "config-logs"
}

# S3 Bucket for Config logs
resource "aws_s3_bucket" "config_logs" {
  bucket = "${local.name_prefix}-config-logs"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-config-logs"
    Type = "compliance"
  })
}

# IAM Role for Config
resource "aws_iam_role" "config" {
  name = "${local.name_prefix}-config-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "config" {
  role       = aws_iam_role.config.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/ConfigRole"
}

# GuardDuty for threat detection
resource "aws_guardduty_detector" "quantumnest_guardduty" {
  enable = true

  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs {
        enable = true
      }
    }
    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = true
        }
      }
    }
  }

  tags = merge(local.common_tags, {
    Type = "security"
  })
}

# Security Hub for centralized security findings
resource "aws_securityhub_account" "quantumnest_securityhub" {
  enable_default_standards = true
}

# Inspector for vulnerability assessments
resource "aws_inspector2_enabler" "quantumnest_inspector" {
  account_ids    = [data.aws_caller_identity.current.account_id]
  resource_types = ["ECR", "EC2"]
}

# WAF for web application protection
resource "aws_wafv2_web_acl" "quantumnest_waf" {
  name  = "${local.name_prefix}-web-acl"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  # Rate limiting rule
  rule {
    name     = "RateLimitRule"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  # AWS Managed Rules
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  # SQL Injection protection
  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "SQLiRuleSetMetric"
      sampled_requests_enabled   = true
    }
  }

  tags = merge(local.common_tags, {
    Type = "security"
  })

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}-web-acl"
    sampled_requests_enabled   = true
  }
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnets" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "database_endpoint" {
  description = "RDS database endpoint"
  value       = module.database.db_instance_endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = module.cache.cache_cluster_address
  sensitive   = true
}

output "kms_key_id" {
  description = "KMS key ID for encryption"
  value       = aws_kms_key.quantumnest_main.key_id
}

output "kms_key_arn" {
  description = "KMS key ARN for encryption"
  value       = aws_kms_key.quantumnest_main.arn
}
