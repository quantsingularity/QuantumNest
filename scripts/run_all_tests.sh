#!/bin/bash

# Run All Tests script for QuantumNest project
# This script executes all unit, integration, and contract tests across the project.

set -euo pipefail

# --- Configuration ---
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
BACKEND_DIR="$PROJECT_ROOT/code/backend"
BLOCKCHAIN_DIR="$PROJECT_ROOT/code/blockchain"
WEB_FRONTEND_DIR="$PROJECT_ROOT/web-frontend"
MOBILE_FRONTEND_DIR="$PROJECT_ROOT/mobile-frontend"

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# --- Utility Functions ---

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to ensure Python virtual environment is set up and activated
ensure_venv() {
  if [ ! -d "$VENV_PATH" ]; then
    echo -e "${BLUE}Creating Python virtual environment at $VENV_PATH...${NC}"
    python3 -m venv "$VENV_PATH"
  fi
  source "$VENV_PATH/bin/activate"
  echo -e "${GREEN}Virtual environment activated.${NC}"
}

# Function to install dependencies
install_dependencies() {
  echo -e "${BLUE}Installing/Updating Python dependencies...${NC}"
  if [ -f "$BACKEND_DIR/requirements.txt" ]; then
    pip install -r "$BACKEND_DIR/requirements.txt" > /dev/null
  else
    echo -e "${RED}Error: Backend requirements.txt not found at $BACKEND_DIR/requirements.txt. Skipping Python dependency install.${NC}"
    exit 1
  fi
  
  echo -e "${BLUE}Installing/Updating Node.js dependencies...${NC}"
  
  # Blockchain
  if [ -d "$BLOCKCHAIN_DIR" ]; then
    echo -e "${BLUE}Installing Blockchain dependencies in $BLOCKCHAIN_DIR...${NC}"
    (cd "$BLOCKCHAIN_DIR" && npm install > /dev/null)
  fi

  # Web Frontend
  if [ -d "$WEB_FRONTEND_DIR" ]; then
    echo -e "${BLUE}Installing Web Frontend dependencies in $WEB_FRONTEND_DIR...${NC}"
    (cd "$WEB_FRONTEND_DIR" && npm install > /dev/null)
  fi

  # Mobile Frontend (using pnpm as per original script's analysis)
  if [ -d "$MOBILE_FRONTEND_DIR" ]; then
    echo -e "${BLUE}Installing Mobile Frontend dependencies in $MOBILE_FRONTEND_DIR...${NC}"
    if command_exists pnpm; then
      (cd "$MOBILE_FRONTEND_DIR" && pnpm install > /dev/null)
    else
      echo -e "${RED}Warning: pnpm not found. Falling back to npm install for $MOBILE_FRONTEND_DIR.${NC}"
      (cd "$MOBILE_FRONTEND_DIR" && npm install > /dev/null)
    fi
  fi
}

# --- Main Execution ---

echo -e "${BLUE}Starting QuantumNest comprehensive test run...${NC}"

# 1. Setup Environment and Dependencies
ensure_venv
install_dependencies

# 2. Run Backend Tests
echo -e "\n${BLUE}Running Backend Tests...${NC}"
(cd "$BACKEND_DIR" && pytest)

# 3. Run Blockchain Tests
echo -e "\n${BLUE}Running Blockchain Tests...${NC}"
(cd "$BLOCKCHAIN_DIR" && npx hardhat test)

# 4. Run Web Frontend Tests
echo -e "\n${BLUE}Running Web Frontend Tests...${NC}"
(cd "$WEB_FRONTEND_DIR" && npm test)

# 5. Run Mobile Frontend Tests
echo -e "\n${BLUE}Running Mobile Frontend Tests...${NC}"
# Assuming mobile frontend uses npm test or similar
(cd "$MOBILE_FRONTEND_DIR" && npm test)

# 6. Finalize
deactivate
echo -e "\n${GREEN}QuantumNest comprehensive test run completed!${NC}"
