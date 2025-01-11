storage "file" {
  path = "/vault/file"
}

listener "tcp" {
  address = "0.0.0.0:8200"
  tls_disable = 0
  tls_cert_file = "/vault/config/cert.pem"
  tls_key_file = "/vault/config/key.pem"
}

seal "awskms" {
  region = "us-west-2"
  kms_key_id = "alias/vault-key"
}

api_addr = "https://vault.indexforge.local:8200"
cluster_addr = "https://vault.indexforge.local:8201"

telemetry {
  prometheus_retention_time = "24h"
  disable_hostname = true
}

ui = true

# Audit logging
audit {
  enabled = true
  type = "file"
  path = "/vault/logs/audit.log"
  rotate_duration = "24h"
  rotate_max_files = 10
}