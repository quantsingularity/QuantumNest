# HashiCorp Vault Configuration for QuantumNest Financial Platform

storage "consul" {
  address = "127.0.0.1:8500"
  path    = "vault/"
  
  # High availability configuration
  ha_enabled = true
  
  # TLS configuration for Consul communication
  tls_ca_file   = "/opt/vault/tls/consul-ca.pem"
  tls_cert_file = "/opt/vault/tls/consul-cert.pem"
  tls_key_file  = "/opt/vault/tls/consul-key.pem"
  tls_min_version = "tls12"
}

# Alternative: AWS S3 backend for cloud-native deployment
# storage "s3" {
#   access_key = "AKIAIOSFODNN7EXAMPLE"
#   secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
#   bucket     = "quantumnest-vault-storage"
#   region     = "us-west-2"
#   encrypt    = true
#   kms_key_id = "arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012"
# }

# Listener configuration with TLS
listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_cert_file = "/opt/vault/tls/vault-cert.pem"
  tls_key_file  = "/opt/vault/tls/vault-key.pem"
  tls_min_version = "tls12"
  tls_cipher_suites = "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384"
  
  # Security headers
  tls_disable_client_certs = false
  tls_require_and_verify_client_cert = true
  tls_client_ca_file = "/opt/vault/tls/client-ca.pem"
}

# Seal configuration using AWS KMS
seal "awskms" {
  region     = "us-west-2"
  kms_key_id = "arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012"
  endpoint   = "https://kms.us-west-2.amazonaws.com"
}

# API address for cluster communication
api_addr = "https://vault.quantumnest.internal:8200"
cluster_addr = "https://vault.quantumnest.internal:8201"

# UI configuration
ui = true

# Telemetry for monitoring
telemetry {
  prometheus_retention_time = "30s"
  disable_hostname = true
  
  # StatsD configuration
  statsd_address = "127.0.0.1:8125"
}

# Logging configuration
log_level = "INFO"
log_format = "json"
log_file = "/var/log/vault/vault.log"
log_rotate_duration = "24h"
log_rotate_max_files = 30

# Performance and security settings
default_lease_ttl = "768h"    # 32 days
max_lease_ttl = "8760h"       # 365 days
disable_mlock = false
disable_cache = false
disable_printable_check = false

# Plugin directory
plugin_directory = "/opt/vault/plugins"

# Raw storage endpoint (disabled for security)
raw_storage_endpoint = false

# Cluster configuration
cluster_name = "quantumnest-vault-cluster"

# License path (for Vault Enterprise)
# license_path = "/opt/vault/license/vault.hclic"

