#!/bin/bash

# Linting and Fixing Script for QuantumNest Project
# This script is designed to be run from the project root (QuantumNest/).

set -euo pipefail # Exit on error, exit on unset variable, fail on pipe error

# --- Configuration ---
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
BACKEND_DIR="$PROJECT_ROOT/code/backend"
QUANTUM_DIR="$PROJECT_ROOT/code/quantum"
WEB_FRONTEND_DIR="$PROJECT_ROOT/web-frontend"
MOBILE_FRONTEND_DIR="$PROJECT_ROOT/mobile-frontend"
BLOCKCHAIN_DIR="$PROJECT_ROOT/code/blockchain"

PYTHON_DIRS=("$BACKEND_DIR" "$QUANTUM_DIR")
JS_DIRS=("$WEB_FRONTEND_DIR/src" "$MOBILE_FRONTEND_DIR/src" "$BLOCKCHAIN_DIR")
YAML_DIRS=("$PROJECT_ROOT/infrastructure/kubernetes" "$PROJECT_ROOT/infrastructure/ansible" "$PROJECT_ROOT/.github/workflows")
TERRAFORM_DIRS=("$PROJECT_ROOT/infrastructure/terraform")

# --- Utility Functions ---

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to ensure Python virtual environment is set up and activated
ensure_venv() {
  echo "Ensuring Python virtual environment is set up..."
  if [ ! -d "$VENV_PATH" ]; then
    echo "Creating Python virtual environment at $VENV_PATH..."
    python3 -m venv "$VENV_PATH"
  fi

  # Activate the virtual environment
  source "$VENV_PATH/bin/activate"
  echo "Virtual environment activated."

  # Install/Update Python dependencies
  echo "Installing/Updating Python dependencies from requirements.txt..."
  pip install --upgrade pip setuptools wheel > /dev/null
  if [ -f "$BACKEND_DIR/requirements.txt" ]; then
    pip install -r "$BACKEND_DIR/requirements.txt"
  else
    echo "Warning: $BACKEND_DIR/requirements.txt not found. Skipping main dependency install."
  fi
  
  # Install linting tools
  echo "Installing/Updating Python linting tools..."
  pip install --upgrade black isort flake8 pylint pyyaml
}

# Function to ensure Node.js dependencies are installed
ensure_node_deps() {
  echo "Ensuring Node.js dependencies are installed..."
  
  # Web Frontend
  if [ -d "$WEB_FRONTEND_DIR" ]; then
    echo "Installing Web Frontend dependencies in $WEB_FRONTEND_DIR..."
    (cd "$WEB_FRONTEND_DIR" && npm install)
  fi

  # Mobile Frontend (using pnpm as per original script's analysis)
  if [ -d "$MOBILE_FRONTEND_DIR" ]; then
    echo "Installing Mobile Frontend dependencies in $MOBILE_FRONTEND_DIR..."
    if command_exists pnpm; then
      (cd "$MOBILE_FRONTEND_DIR" && pnpm install)
    else
      echo "Warning: pnpm not found. Falling back to npm install for $MOBILE_FRONTEND_DIR."
      (cd "$MOBILE_FRONTEND_DIR" && npm install)
    fi
  fi

  # Blockchain
  if [ -d "$BLOCKCHAIN_DIR" ]; then
    echo "Installing Blockchain dependencies in $BLOCKCHAIN_DIR..."
    (cd "$BLOCKCHAIN_DIR" && npm install)
  fi
}

# --- Main Execution ---

echo "----------------------------------------"
echo "Starting linting and fixing process for QuantumNest..."
echo "----------------------------------------"

# 1. Environment Setup
ensure_venv
ensure_node_deps

# 2. Python Linting
echo "----------------------------------------"
echo "Running Python linting tools..."

for dir in "${PYTHON_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    echo "Processing Python files in $dir..."
    # Black (code formatter)
    python -m black "$dir"
    # isort (import sorter)
    python -m isort "$dir"
    # flake8 (linter)
    python -m flake8 "$dir"
    # pylint (more comprehensive linter)
    find "$dir" -type f -name "*.py" | xargs python -m pylint --disable=C0111,C0103,C0303,W0621,C0301,W0612,W0611,R0913,R0914,R0915
  else
    echo "Directory $dir not found. Skipping Python linting."
  fi
done

# 3. JavaScript/TypeScript Linting
echo "----------------------------------------"
echo "Running JavaScript/TypeScript linting tools..."

for dir in "${JS_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    echo "Processing JavaScript/TypeScript files in $dir..."
    (
      cd "$dir"
      # ESLint
      npx eslint . --ext .js,.jsx,.ts,.tsx --fix
      # Prettier
      npx prettier --write "**/*.{js,jsx,ts,tsx,json,css,scss,md}" --ignore-unknown
    )
  else
    echo "Directory $dir not found. Skipping JS/TS linting."
  fi
done

# 4. YAML Linting
echo "----------------------------------------"
echo "Running YAML linting tools..."

if command_exists yamllint; then
  echo "Running yamllint for YAML files..."
  for dir in "${YAML_DIRS[@]}"; do
    if [ -d "$dir" ]; then
      yamllint "$dir"
    else
      echo "Directory $dir not found. Skipping yamllint."
    fi
  done
else
  echo "yamllint not installed. Performing basic YAML validation using Python..."
  for dir in "${YAML_DIRS[@]}"; do
    if [ -d "$dir" ]; then
      find "$dir" -type f \( -name "*.yaml" -o -name "*.yml" \) -exec python -c "import yaml; yaml.safe_load(open('{}', 'r'))" \;
    else
      echo "Directory $dir not found. Skipping YAML validation."
    fi
  done
fi

# 5. Terraform Linting
echo "----------------------------------------"
echo "Running Terraform linting tools..."

if command_exists terraform; then
  echo "Running terraform fmt and validate for Terraform files..."
  for dir in "${TERRAFORM_DIRS[@]}"; do
    if [ -d "$dir" ]; then
      echo "Processing Terraform files in $dir..."
      (cd "$dir" && terraform fmt -recursive && terraform init -backend=false && terraform validate)
    else
      echo "Directory $dir not found. Skipping Terraform processing."
    fi
  done
else
  echo "Skipping Terraform linting (terraform not installed)."
fi

# 6. Common Fixes for All File Types
echo "----------------------------------------"
echo "Applying common fixes to all file types..."

# Fix trailing whitespace and ensure newline at end of file
find "$PROJECT_ROOT" -type f \( -name "*.py" -o -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" -o -name "*.yaml" -o -name "*.yml" -o -name "*.tf" -o -name "*.tfvars" \) \
  -not -path "*/node_modules/*" -not -path "*/venv/*" -not -path "*/dist/*" -not -path "*/.next/*" \
  -exec sed -i 's/[ \t]*$//' {} \; \
  -exec sh -c '[ -n "$(tail -c1 "$1")" ] && echo "" >> "$1"' sh {} \;

echo "Common fixes completed."

# Deactivate virtual environment
deactivate

echo "----------------------------------------"
echo "Linting and fixing process for QuantumNest completed!"
echo "----------------------------------------"
