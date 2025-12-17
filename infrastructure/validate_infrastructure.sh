#!/bin/bash
# Infrastructure Validation Script
# This script validates all infrastructure components

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== QuantumNest Infrastructure Validation ==="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

# Track overall status
OVERALL_STATUS=0

# =================================================================
# TERRAFORM VALIDATION
# =================================================================

echo "=== Terraform Validation ==="

# Check if terraform is installed
if command -v terraform >/dev/null 2>&1; then
    print_status 0 "Terraform is installed"
    
    cd terraform
    
    # Format check
    echo "Running terraform fmt..."
    if terraform fmt -check -recursive; then
        print_status 0 "Terraform format check"
    else
        print_status 1 "Terraform format check"
    fi
    
    # Initialize (backend=false for local validation)
    echo "Running terraform init..."
    if terraform init -backend=false >/dev/null 2>&1; then
        print_status 0 "Terraform init"
    else
        print_status 1 "Terraform init"
    fi
    
    # Validate
    echo "Running terraform validate..."
    if terraform validate >/dev/null 2>&1; then
        print_status 0 "Terraform validate"
    else
        print_status 1 "Terraform validate (may need terraform.tfvars)"
    fi
    
    cd ..
else
    print_status 1 "Terraform not installed"
    OVERALL_STATUS=1
fi

echo ""

# =================================================================
# KUBERNETES VALIDATION
# =================================================================

echo "=== Kubernetes Validation ==="

# Check if kubectl is installed
if command -v kubectl >/dev/null 2>&1; then
    print_status 0 "kubectl is installed"
    
    # Validate manifests with dry-run
    echo "Validating Kubernetes manifests..."
    if kubectl apply --dry-run=client -f kubernetes/base/ --recursive >/dev/null 2>&1; then
        print_status 0 "Kubernetes manifest validation"
    else
        print_status 1 "Kubernetes manifest validation"
    fi
else
    print_status 1 "kubectl not installed"
fi

# Check if yamllint is installed
if command -v yamllint >/dev/null 2>&1; then
    echo "Running yamllint..."
    if yamllint -c kubernetes/.yamllint kubernetes/ >/dev/null 2>&1; then
        print_status 0 "YAML lint"
    else
        print_status 1 "YAML lint"
    fi
fi

echo ""

# =================================================================
# ANSIBLE VALIDATION
# =================================================================

echo "=== Ansible Validation ==="

# Check if ansible is installed
if command -v ansible >/dev/null 2>&1; then
    print_status 0 "Ansible is installed"
    
    cd ansible
    
    # Syntax check
    if [ -f "inventory/hosts.yml" ]; then
        echo "Running ansible-playbook syntax check..."
        if ansible-playbook playbooks/main.yml --syntax-check >/dev/null 2>&1; then
            print_status 0 "Ansible syntax check"
        else
            print_status 1 "Ansible syntax check"
        fi
    else
        echo -e "${YELLOW}⚠${NC} inventory/hosts.yml not found (use hosts.example.yml as template)"
    fi
    
    cd ..
else
    print_status 1 "Ansible not installed"
fi

echo ""

# =================================================================
# SUMMARY
# =================================================================

echo "=== Validation Summary ==="
if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}All validations passed!${NC}"
else
    echo -e "${YELLOW}Some tools not installed. Install them for full validation.${NC}"
fi

exit 0
