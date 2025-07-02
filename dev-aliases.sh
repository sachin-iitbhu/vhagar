#!/bin/bash

# Development Aliases for Vhagar Project
# This script provides convenient aliases to run all three services with auto-reload

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Base directories
VHAGAR_DIR="/Users/sachinmittal/vhagar"
FRONTEND_DIR="/Users/sachinmittal/comp-peek-salary-view"

# Alias functions
rag() {
    print_info "Starting Python RAG Agent with auto-reload on port 8000..."
    cd "$VHAGAR_DIR"
    if [ -d "venv" ]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_warning "Virtual environment not found, using system Python"
    fi
    python3 run_dev.py
}

go-backend() {
    print_info "Starting Go Backend with auto-reload on port 8081..."
    cd "$VHAGAR_DIR"
    ./run_go_dev.sh
}

frontend() {
    print_info "Starting Vite Frontend with auto-reload on port 8080..."
    cd "$FRONTEND_DIR"
    npm run dev
}

# Combined function to show all options
vhagar() {
    echo ""
    echo -e "${BLUE}🚀 Vhagar Development Commands${NC}"
    echo "================================"
    echo ""
    echo -e "${GREEN}Available commands:${NC}"
    echo "  rag         - Start Python RAG Agent (port 8000)"
    echo "  go-backend  - Start Go Backend (port 8081)"
    echo "  frontend    - Start Vite Frontend (port 8080)"
    echo "  vhagar-all  - Show instructions to run all services"
    echo "  vhagar-status - Check which ports are in use"
    echo ""
    echo -e "${YELLOW}Usage examples:${NC}"
    echo "  $ rag"
    echo "  $ go-backend"
    echo "  $ frontend"
    echo ""
}

# Function to run all services (instructions)
vhagar-all() {
    echo ""
    echo -e "${BLUE}🚀 Starting All Vhagar Services${NC}"
    echo "==============================="
    echo ""
    echo -e "${YELLOW}Open 3 separate terminals and run:${NC}"
    echo ""
    echo -e "${GREEN}Terminal 1 (Python RAG):${NC}"
    echo "  $ rag"
    echo ""
    echo -e "${GREEN}Terminal 2 (Go Backend):${NC}"
    echo "  $ go-backend"
    echo ""
    echo -e "${GREEN}Terminal 3 (Frontend):${NC}"
    echo "  $ frontend"
    echo ""
    echo -e "${BLUE}After all services are running:${NC}"
    echo "  🐍 Python RAG:  http://localhost:8000"
    echo "  🔗 Go Backend:  http://localhost:8081"
    echo "  🎨 Frontend:    http://localhost:8080"
    echo ""
}

# Function to check service status
vhagar-status() {
    echo ""
    echo -e "${BLUE}📊 Vhagar Services Status${NC}"
    echo "========================="
    echo ""
    
    # Check port 8000 (Python RAG)
    if lsof -ti:8000 > /dev/null 2>&1; then
        print_success "Port 8000 (Python RAG): RUNNING"
    else
        print_warning "Port 8000 (Python RAG): NOT RUNNING"
    fi
    
    # Check port 8081 (Go Backend)
    if lsof -ti:8081 > /dev/null 2>&1; then
        print_success "Port 8081 (Go Backend): RUNNING"
    else
        print_warning "Port 8081 (Go Backend): NOT RUNNING"
    fi
    
    # Check port 8080 (Frontend)
    if lsof -ti:8080 > /dev/null 2>&1; then
        print_success "Port 8080 (Frontend): RUNNING"
    else
        print_warning "Port 8080 (Frontend): NOT RUNNING"
    fi
    echo ""
}

# Help function
vhagar-help() {
    vhagar
}

# If script is sourced, make functions available
# If script is executed directly, show help
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    vhagar
fi
