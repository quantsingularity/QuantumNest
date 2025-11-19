# Vault Policies for QuantumNest Financial Platform

# Admin Policy - Full access for Vault administrators
path "auth/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

path "sys/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

path "secret/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "pki/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

# Financial Data Access Policy - For applications handling financial data
path "secret/data/financial/*" {
  capabilities = ["read", "list"]
  required_parameters = ["version"]

  # Require MFA for access
  control_group = {
    factor "mfa" {
      identity_groups = ["financial-approvers"]
    }
  }
}

path "secret/metadata/financial/*" {
  capabilities = ["read", "list"]
}

# Database Credentials Policy - For database access
path "database/creds/quantumnest-db-*" {
  capabilities = ["read"]

  # Time-based access control
  allowed_parameters = {
    "ttl" = ["1h", "2h", "4h"]
  }

  # IP restriction
  bound_cidrs = ["10.0.0.0/8", "172.16.0.0/12"]
}

path "database/config/*" {
  capabilities = ["read", "list"]
}

# PKI Policy - For certificate management
path "pki/issue/quantumnest-server" {
  capabilities = ["create", "update"]

  allowed_parameters = {
    "common_name" = ["*.quantumnest.internal", "*.quantumnest.com"]
    "alt_names" = ["*.quantumnest.internal", "*.quantumnest.com"]
    "ttl" = ["720h"]  # 30 days max
  }
}

path "pki/cert/ca" {
  capabilities = ["read"]
}

# Application Policy - For QuantumNest applications
path "secret/data/app/quantumnest/*" {
  capabilities = ["read"]

  # Require specific entity metadata
  required_parameters = ["entity_id"]
}

path "secret/metadata/app/quantumnest/*" {
  capabilities = ["read", "list"]
}

# Kubernetes Auth Policy - For Kubernetes service accounts
path "auth/kubernetes/role/*" {
  capabilities = ["read", "list"]
}

path "auth/kubernetes/login" {
  capabilities = ["create", "update"]
}

# Transit Encryption Policy - For encryption as a service
path "transit/encrypt/quantumnest-*" {
  capabilities = ["create", "update"]
}

path "transit/decrypt/quantumnest-*" {
  capabilities = ["create", "update"]
}

path "transit/datakey/plaintext/quantumnest-*" {
  capabilities = ["create", "update"]
}

# Audit Policy - For compliance and security teams
path "sys/audit" {
  capabilities = ["read", "list"]
}

path "sys/audit-hash" {
  capabilities = ["create", "update"]
}

# Identity Policy - For identity management
path "identity/entity/id/*" {
  capabilities = ["read", "list"]
}

path "identity/group/id/*" {
  capabilities = ["read", "list"]
}

# KV Version 2 Specific Policies
path "secret/data/prod/*" {
  capabilities = ["read"]

  # Production access requires approval
  control_group = {
    factor "approvers" {
      identity_groups = ["production-approvers"]
      approvals = 2
    }
  }
}

path "secret/data/staging/*" {
  capabilities = ["read", "create", "update"]

  # Staging environment access
  allowed_parameters = {
    "version" = []
  }
}

path "secret/data/dev/*" {
  capabilities = ["read", "create", "update", "delete"]

  # Development environment - more permissive
}

# Compliance and Audit Paths
path "secret/data/compliance/*" {
  capabilities = ["read", "list"]

  # Only compliance officers can access
  required_parameters = ["compliance_officer_id"]
}

path "secret/data/audit/*" {
  capabilities = ["read", "list"]

  # Audit trail access
  bound_cidrs = ["10.0.100.0/24"]  # Audit network only
}
