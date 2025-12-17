#!/bin/bash
# Infrastructure Deployment Script
# This script helps deploy infrastructure components

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== QuantumNest Infrastructure Deployment ===${NC}"
echo ""

# Function to print menu
print_menu() {
    echo "Select deployment target:"
    echo "  1) Terraform (Plan)"
    echo "  2) Terraform (Apply)"
    echo "  3) Kubernetes (Dry-run)"
    echo "  4) Kubernetes (Apply)"
    echo "  5) Ansible (Check mode)"
    echo "  6) Ansible (Execute)"
    echo "  7) Full validation"
    echo "  8) Exit"
    echo ""
}

# Function to deploy terraform
deploy_terraform() {
    local action=$1
    echo -e "${BLUE}=== Terraform ${action} ===${NC}"
    
    cd terraform
    
    # Check for tfvars file
    if [ ! -f "terraform.tfvars" ]; then
        echo -e "${YELLOW}⚠ terraform.tfvars not found${NC}"
        echo "Create it from terraform.tfvars.example"
        echo "cp terraform.tfvars.example terraform.tfvars"
        echo "Then edit terraform.tfvars with your values"
        cd ..
        return 1
    fi
    
    # Initialize
    echo "Initializing Terraform..."
    terraform init
    
    # Plan or Apply
    if [ "$action" == "plan" ]; then
        terraform plan -out=tfplan
        echo -e "${GREEN}✓ Plan saved to tfplan${NC}"
    else
        echo -e "${YELLOW}This will apply changes to your infrastructure.${NC}"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" == "yes" ]; then
            terraform apply
            echo -e "${GREEN}✓ Terraform applied successfully${NC}"
        else
            echo "Aborted."
        fi
    fi
    
    cd ..
}

# Function to deploy kubernetes
deploy_kubernetes() {
    local mode=$1
    echo -e "${BLUE}=== Kubernetes ${mode} ===${NC}"
    
    # Check kubectl connection
    if ! kubectl cluster-info >/dev/null 2>&1; then
        echo -e "${RED}✗ Cannot connect to Kubernetes cluster${NC}"
        echo "Please configure kubectl first"
        return 1
    fi
    
    echo "Connected to: $(kubectl config current-context)"
    echo ""
    
    # Select environment
    echo "Select environment:"
    echo "  1) Development"
    echo "  2) Staging"
    echo "  3) Production"
    read -p "Choice: " env_choice
    
    case $env_choice in
        1) env="dev" ;;
        2) env="staging" ;;
        3) env="production" ;;
        *) echo "Invalid choice"; return 1 ;;
    esac
    
    # Check for secrets
    echo -e "${YELLOW}⚠ Make sure secrets are created first!${NC}"
    echo "See kubernetes/base/app-secrets.example.yaml"
    read -p "Secrets created? (yes/no): " secrets_confirm
    
    if [ "$secrets_confirm" != "yes" ]; then
        echo "Please create secrets first"
        return 1
    fi
    
    # Deploy
    if [ "$mode" == "dry-run" ]; then
        kubectl apply --dry-run=client -k kubernetes/environments/${env}/
    else
        echo -e "${YELLOW}This will deploy to ${env} environment.${NC}"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" == "yes" ]; then
            kubectl apply -k kubernetes/environments/${env}/
            echo -e "${GREEN}✓ Deployed to ${env}${NC}"
            echo ""
            echo "Check status:"
            echo "  kubectl get pods -n quantumnest-${env}"
        else
            echo "Aborted."
        fi
    fi
}

# Function to deploy ansible
deploy_ansible() {
    local mode=$1
    echo -e "${BLUE}=== Ansible ${mode} ===${NC}"
    
    cd ansible
    
    # Check for inventory
    if [ ! -f "inventory/hosts.yml" ]; then
        echo -e "${YELLOW}⚠ inventory/hosts.yml not found${NC}"
        echo "Create it from inventory/hosts.example.yml"
        cd ..
        return 1
    fi
    
    # Run playbook
    if [ "$mode" == "check" ]; then
        ansible-playbook playbooks/main.yml --check --diff
    else
        echo -e "${YELLOW}This will configure your servers.${NC}"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" == "yes" ]; then
            ansible-playbook playbooks/main.yml
            echo -e "${GREEN}✓ Ansible completed successfully${NC}"
        else
            echo "Aborted."
        fi
    fi
    
    cd ..
}

# Main menu loop
while true; do
    print_menu
    read -p "Choice: " choice
    echo ""
    
    case $choice in
        1) deploy_terraform "plan" ;;
        2) deploy_terraform "apply" ;;
        3) deploy_kubernetes "dry-run" ;;
        4) deploy_kubernetes "apply" ;;
        5) deploy_ansible "check" ;;
        6) deploy_ansible "execute" ;;
        7) ./validate_infrastructure.sh ;;
        8) echo "Goodbye!"; exit 0 ;;
        *) echo -e "${RED}Invalid choice${NC}" ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
    echo ""
done
