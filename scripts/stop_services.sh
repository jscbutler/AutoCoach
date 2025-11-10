#!/bin/bash
# AutoCoach - Stop all services

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Source component scripts
source "$SCRIPT_DIR/script_components/common.sh"
source "$SCRIPT_DIR/script_components/backend.sh"
source "$SCRIPT_DIR/script_components/frontend.sh"

log_header "Stopping AutoCoach Services"

# Stop services
stop_frontend
stop_fastapi

# Clear PID tracking
clear_pids

# Kill any remaining AutoCoach processes on known ports
if is_port_in_use $AUTOCOACH_PORT; then
    log_info "Killing process on port $AUTOCOACH_PORT..."
    lsof -ti:$AUTOCOACH_PORT | xargs kill -9 2>/dev/null
fi

if is_port_in_use $FRONTEND_PORT; then
    log_info "Killing process on port $FRONTEND_PORT..."
    lsof -ti:$FRONTEND_PORT | xargs kill -9 2>/dev/null
fi

log_success "All AutoCoach services stopped"
echo ""

