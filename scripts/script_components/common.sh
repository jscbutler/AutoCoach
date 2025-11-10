#!/bin/bash
# Common utilities for AutoCoach startup scripts
# Shared functions and variables

# Colors for output
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export NC='\033[0m' # No Color

# Project paths
export AUTOCOACH_ROOT="/Users/jeffbutler/Dev/AutoCoach"
export EVE_PROJECT="/Users/jeffbutler/Dev/Dev/eve_py"
export EVE_TUNNEL_CONFIG="$EVE_PROJECT/config/cloudflare-tunnel.yaml"
export EVE_TUNNEL_ID="5a4becbf-b84e-4e90-80d0-f4f8ec2ffc20"

# Service ports
export AUTOCOACH_PORT=8000
export POSTGRES_PORT=5432

# Functions

print_header() {
    echo ""
    echo "================================================================================"
    echo "  $1"
    echo "================================================================================"
    echo ""
}

print_section() {
    echo ""
    echo "--- $1 ---"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

# Check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check if a process is running on a port
port_in_use() {
    local port=$1
    lsof -i :"$port" &> /dev/null
}

# Get PID of process on port
get_pid_on_port() {
    local port=$1
    lsof -t -i :"$port" 2>/dev/null
}

# Check if a process is running by name
process_running() {
    local name=$1
    ps aux | grep -v grep | grep -q "$name"
}

# Wait for a port to become available
wait_for_port() {
    local port=$1
    local timeout=${2:-30}
    local elapsed=0
    
    while ! port_in_use "$port"; do
        if [ $elapsed -ge $timeout ]; then
            return 1
        fi
        sleep 1
        ((elapsed++))
    done
    return 0
}

# Check if virtual environment exists
check_venv() {
    local venv_path="$AUTOCOACH_ROOT/ac_env"
    
    if [ ! -d "$venv_path" ]; then
        print_error "Virtual environment not found at: $venv_path"
        echo ""
        echo "Create it with:"
        echo "  cd $AUTOCOACH_ROOT"
        echo "  python3 -m venv ac_env"
        echo "  source ac_env/bin/activate"
        echo "  pip install -r requirements.txt"
        echo ""
        return 1
    fi
    
    return 0
}

# Check if .env file exists
check_env_file() {
    local env_file="$AUTOCOACH_ROOT/.env"
    
    if [ ! -f "$env_file" ]; then
        print_warning ".env file not found"
        echo ""
        echo "Create it with:"
        echo "  cd $AUTOCOACH_ROOT"
        echo "  cp env.template .env"
        echo "  nano .env  # Add your TrainingPeaks credentials"
        echo ""
        return 1
    fi
    
    return 0
}

# Activate virtual environment
activate_venv() {
    local venv_path="$AUTOCOACH_ROOT/ac_env"
    
    if [ -f "$venv_path/bin/activate" ]; then
        source "$venv_path/bin/activate"
        return 0
    fi
    
    return 1
}

# Check if a service is healthy
check_service_health() {
    local url=$1
    local max_attempts=${2:-10}
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "$url" &> /dev/null; then
            return 0
        fi
        sleep 1
        ((attempt++))
    done
    
    return 1
}

# Kill process on port
kill_port() {
    local port=$1
    local pid=$(get_pid_on_port "$port")
    
    if [ -n "$pid" ]; then
        print_info "Killing process $pid on port $port"
        kill "$pid" 2>/dev/null
        sleep 2
        
        # Force kill if still running
        if port_in_use "$port"; then
            kill -9 "$pid" 2>/dev/null
        fi
    fi
}

# Store PID for cleanup
store_pid() {
    local service_name=$1
    local pid=$2
    local pid_file="$AUTOCOACH_ROOT/.pids/$service_name.pid"
    
    mkdir -p "$AUTOCOACH_ROOT/.pids"
    echo "$pid" > "$pid_file"
}

# Get stored PID
get_stored_pid() {
    local service_name=$1
    local pid_file="$AUTOCOACH_ROOT/.pids/$service_name.pid"
    
    if [ -f "$pid_file" ]; then
        cat "$pid_file"
    fi
}

# Clean up PIDs
cleanup_pids() {
    rm -rf "$AUTOCOACH_ROOT/.pids" 2>/dev/null
}

export -f print_header
export -f print_section
export -f print_success
export -f print_warning
export -f print_error
export -f print_info
export -f command_exists
export -f port_in_use
export -f get_pid_on_port
export -f process_running
export -f wait_for_port
export -f check_venv
export -f check_env_file
export -f activate_venv
export -f check_service_health
export -f kill_port
export -f store_pid
export -f get_stored_pid
export -f cleanup_pids
