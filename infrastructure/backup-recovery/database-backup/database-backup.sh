#!/bin/bash
# QuantumNest Database Backup Script for Financial Services Compliance
# This script performs comprehensive database backups with encryption and compliance features

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/backup-config.conf"
LOG_FILE="/var/log/quantumnest/database-backup.log"
AUDIT_LOG="/var/log/quantumnest/backup-audit.log"

# Source configuration
if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
else
    echo "ERROR: Configuration file not found: $CONFIG_FILE" >&2
    exit 1
fi

# Default configuration values
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-quantumnest_prod}"
DB_USER="${DB_USER:-backup_user}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/quantumnest}"
S3_BUCKET="${S3_BUCKET:-quantumnest-backups-prod}"
ENCRYPTION_KEY_ID="${ENCRYPTION_KEY_ID:-arn:aws:kms:us-west-2:123456789012:key/12345678-1234-1234-1234-123456789012}"
RETENTION_DAYS="${RETENTION_DAYS:-2555}"  # 7 years for financial compliance
BACKUP_TYPE="${BACKUP_TYPE:-full}"  # full, incremental, differential

# Logging functions
log() {
    echo "$(date -Iseconds) [INFO] $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo "$(date -Iseconds) [ERROR] $*" | tee -a "$LOG_FILE" >&2
}

audit_log() {
    echo "$(date -Iseconds) | BACKUP_AUDIT | $*" >> "$AUDIT_LOG"
}

# Compliance and security functions
verify_compliance() {
    log "Verifying compliance requirements..."

    # Check encryption key availability
    if ! aws kms describe-key --key-id "$ENCRYPTION_KEY_ID" >/dev/null 2>&1; then
        log_error "Encryption key not accessible: $ENCRYPTION_KEY_ID"
        return 1
    fi

    # Verify backup directory permissions
    if [[ ! -d "$BACKUP_DIR" ]]; then
        mkdir -p "$BACKUP_DIR"
        chmod 700 "$BACKUP_DIR"
    fi

    # Check disk space (require at least 50GB free)
    local available_space
    available_space=$(df "$BACKUP_DIR" | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 52428800 ]]; then  # 50GB in KB
        log_error "Insufficient disk space for backup: ${available_space}KB available"
        return 1
    fi

    log "Compliance verification completed"
    return 0
}

# Database connection test
test_database_connection() {
    log "Testing database connection..."

    if ! PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" >/dev/null 2>&1; then
        log_error "Database connection failed"
        return 1
    fi

    log "Database connection successful"
    return 0
}

# Generate backup filename with compliance metadata
generate_backup_filename() {
    local backup_type="$1"
    local timestamp
    timestamp=$(date +"%Y%m%d_%H%M%S")

    echo "${DB_NAME}_${backup_type}_${timestamp}.sql.gz.enc"
}

# Perform database backup
perform_backup() {
    local backup_type="$1"
    local backup_filename
    local backup_path
    local temp_file

    backup_filename=$(generate_backup_filename "$backup_type")
    backup_path="${BACKUP_DIR}/${backup_filename}"
    temp_file=$(mktemp)

    log "Starting $backup_type backup: $backup_filename"
    audit_log "BACKUP_START | $backup_type | $backup_filename | $DB_NAME"

    # Create backup based on type
    case "$backup_type" in
        "full")
            PGPASSWORD="$DB_PASSWORD" pg_dump \
                -h "$DB_HOST" \
                -p "$DB_PORT" \
                -U "$DB_USER" \
                -d "$DB_NAME" \
                --verbose \
                --no-password \
                --format=custom \
                --compress=9 \
                --no-privileges \
                --no-owner \
                --create \
                --clean \
                --if-exists \
                > "$temp_file"
            ;;
        "incremental")
            # WAL-based incremental backup
            PGPASSWORD="$DB_PASSWORD" pg_basebackup \
                -h "$DB_HOST" \
                -p "$DB_PORT" \
                -U "$DB_USER" \
                -D "$temp_file" \
                --format=tar \
                --gzip \
                --progress \
                --verbose \
                --wal-method=stream
            ;;
        *)
            log_error "Unknown backup type: $backup_type"
            rm -f "$temp_file"
            return 1
            ;;
    esac

    # Verify backup file was created
    if [[ ! -s "$temp_file" ]]; then
        log_error "Backup file is empty or was not created"
        rm -f "$temp_file"
        return 1
    fi

    # Calculate backup size and checksum
    local backup_size
    local backup_checksum
    backup_size=$(stat -f%z "$temp_file" 2>/dev/null || stat -c%s "$temp_file")
    backup_checksum=$(sha256sum "$temp_file" | cut -d' ' -f1)

    log "Backup created successfully: ${backup_size} bytes, SHA256: ${backup_checksum}"

    # Encrypt backup using AWS KMS
    log "Encrypting backup with KMS key: $ENCRYPTION_KEY_ID"
    aws kms encrypt \
        --key-id "$ENCRYPTION_KEY_ID" \
        --plaintext "fileb://$temp_file" \
        --output text \
        --query CiphertextBlob \
        | base64 --decode > "$backup_path"

    # Verify encrypted backup
    if [[ ! -s "$backup_path" ]]; then
        log_error "Encrypted backup file is empty or was not created"
        rm -f "$temp_file" "$backup_path"
        return 1
    fi

    # Create backup metadata
    create_backup_metadata "$backup_filename" "$backup_size" "$backup_checksum" "$backup_type"

    # Clean up temporary file
    rm -f "$temp_file"

    log "Backup encryption completed: $backup_path"
    audit_log "BACKUP_COMPLETE | $backup_type | $backup_filename | $backup_size | $backup_checksum"

    return 0
}

# Create backup metadata for compliance
create_backup_metadata() {
    local filename="$1"
    local size="$2"
    local checksum="$3"
    local type="$4"
    local metadata_file="${BACKUP_DIR}/${filename}.metadata"

    cat > "$metadata_file" << EOF
{
    "backup_filename": "$filename",
    "backup_type": "$type",
    "database_name": "$DB_NAME",
    "database_host": "$DB_HOST",
    "backup_timestamp": "$(date -Iseconds)",
    "backup_size_bytes": $size,
    "sha256_checksum": "$checksum",
    "encryption_key_id": "$ENCRYPTION_KEY_ID",
    "retention_until": "$(date -d "+$RETENTION_DAYS days" -Iseconds)",
    "compliance_standards": ["SOX", "PCI-DSS", "GDPR", "FINRA"],
    "data_classification": "confidential",
    "backup_operator": "$(whoami)",
    "backup_host": "$(hostname)",
    "backup_version": "1.0.0"
}
EOF

    log "Backup metadata created: $metadata_file"
}

# Upload backup to S3 with compliance tags
upload_to_s3() {
    local backup_filename="$1"
    local backup_path="${BACKUP_DIR}/${backup_filename}"
    local metadata_path="${backup_path}.metadata"
    local s3_key="database-backups/$(date +%Y/%m/%d)/${backup_filename}"

    log "Uploading backup to S3: s3://${S3_BUCKET}/${s3_key}"

    # Upload backup file
    aws s3 cp "$backup_path" "s3://${S3_BUCKET}/${s3_key}" \
        --server-side-encryption aws:kms \
        --ssekms-key-id "$ENCRYPTION_KEY_ID" \
        --metadata "backup-type=${BACKUP_TYPE},database=${DB_NAME},compliance=financial" \
        --tagging "Environment=production&DataClassification=confidential&Compliance=SOX,PCI-DSS,GDPR,FINRA&RetentionDays=${RETENTION_DAYS}"

    # Upload metadata file
    aws s3 cp "$metadata_path" "s3://${S3_BUCKET}/${s3_key}.metadata" \
        --server-side-encryption aws:kms \
        --ssekms-key-id "$ENCRYPTION_KEY_ID"

    log "Backup uploaded successfully to S3"
    audit_log "BACKUP_UPLOADED | $backup_filename | s3://${S3_BUCKET}/${s3_key}"

    return 0
}

# Verify backup integrity
verify_backup_integrity() {
    local backup_filename="$1"
    local backup_path="${BACKUP_DIR}/${backup_filename}"
    local metadata_path="${backup_path}.metadata"

    log "Verifying backup integrity: $backup_filename"

    # Check if backup file exists and is not empty
    if [[ ! -s "$backup_path" ]]; then
        log_error "Backup file is missing or empty: $backup_path"
        return 1
    fi

    # Check if metadata file exists
    if [[ ! -f "$metadata_path" ]]; then
        log_error "Backup metadata is missing: $metadata_path"
        return 1
    fi

    # Decrypt and verify backup (test decryption without full restore)
    local temp_decrypt
    temp_decrypt=$(mktemp)

    if aws kms decrypt \
        --ciphertext-blob "fileb://$backup_path" \
        --output text \
        --query Plaintext \
        | base64 --decode > "$temp_decrypt" 2>/dev/null; then

        # Verify decrypted file is valid
        if [[ -s "$temp_decrypt" ]]; then
            log "Backup integrity verification successful"
            rm -f "$temp_decrypt"
            return 0
        else
            log_error "Decrypted backup file is empty"
            rm -f "$temp_decrypt"
            return 1
        fi
    else
        log_error "Failed to decrypt backup for verification"
        rm -f "$temp_decrypt"
        return 1
    fi
}

# Clean up old backups based on retention policy
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days"

    # Local cleanup
    find "$BACKUP_DIR" -name "*.sql.gz.enc" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.metadata" -mtime +$RETENTION_DAYS -delete

    # S3 cleanup (using lifecycle policies is preferred, but manual cleanup as backup)
    local cutoff_date
    cutoff_date=$(date -d "-$RETENTION_DAYS days" +%Y-%m-%d)

    aws s3api list-objects-v2 \
        --bucket "$S3_BUCKET" \
        --prefix "database-backups/" \
        --query "Contents[?LastModified<='$cutoff_date'].Key" \
        --output text | \
    while read -r key; do
        if [[ -n "$key" && "$key" != "None" ]]; then
            aws s3 rm "s3://${S3_BUCKET}/${key}"
            audit_log "BACKUP_DELETED | $key | retention_policy"
        fi
    done

    log "Backup cleanup completed"
}

# Send backup notifications
send_notifications() {
    local status="$1"
    local backup_filename="$2"
    local message

    if [[ "$status" == "success" ]]; then
        message="✅ Database backup completed successfully: $backup_filename"
    else
        message="❌ Database backup failed: $backup_filename"
    fi

    # Slack notification
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL"
    fi

    # Email notification
    if [[ -n "${EMAIL_RECIPIENTS:-}" ]]; then
        echo "$message" | mail -s "QuantumNest Database Backup Status" "$EMAIL_RECIPIENTS"
    fi

    log "Notifications sent"
}

# Main backup execution
main() {
    local backup_filename
    local exit_code=0

    log "Starting QuantumNest database backup process"
    audit_log "BACKUP_PROCESS_START | $BACKUP_TYPE | $DB_NAME"

    # Pre-backup checks
    if ! verify_compliance; then
        log_error "Compliance verification failed"
        exit_code=1
    elif ! test_database_connection; then
        log_error "Database connection test failed"
        exit_code=1
    else
        # Perform backup
        backup_filename=$(generate_backup_filename "$BACKUP_TYPE")

        if perform_backup "$BACKUP_TYPE"; then
            if verify_backup_integrity "$backup_filename"; then
                if upload_to_s3 "$backup_filename"; then
                    cleanup_old_backups
                    send_notifications "success" "$backup_filename"
                    log "Backup process completed successfully"
                else
                    log_error "S3 upload failed"
                    exit_code=1
                fi
            else
                log_error "Backup integrity verification failed"
                exit_code=1
            fi
        else
            log_error "Backup creation failed"
            exit_code=1
        fi
    fi

    if [[ $exit_code -ne 0 ]]; then
        send_notifications "failure" "${backup_filename:-unknown}"
    fi

    audit_log "BACKUP_PROCESS_END | $BACKUP_TYPE | $DB_NAME | exit_code:$exit_code"
    log "Backup process finished with exit code: $exit_code"

    exit $exit_code
}

# Execute main function
main "$@"
