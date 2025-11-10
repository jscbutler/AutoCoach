#!/bin/bash
# Frontend services management for AutoCoach

# Source common functions
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

start_frontend() {
    log_header "Starting Frontend Services"
    
    # Check if React app exists
    if [ ! -d "$PROJECT_ROOT/frontend" ]; then
        log_info "Frontend not yet implemented"
        log_info "Future: React app will run on port $FRONTEND_PORT"
        return 0
    fi
    
    # Check if already running
    if is_port_in_use $FRONTEND_PORT; then
        log_warning "Port $FRONTEND_PORT already in use"
        return 1
    fi
    
    log_info "Starting React frontend on port $FRONTEND_PORT..."
    
    cd "$PROJECT_ROOT/frontend"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_info "Installing dependencies..."
        npm install
    fi
    
    # Start React app in background
    PORT=$FRONTEND_PORT npm start > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
    local pid=$!
    
    # Wait for frontend to start
    if wait_for_port $FRONTEND_PORT "React Frontend" 30; then
        add_pid "frontend" $pid
        log_success "Frontend started (PID: $pid)"
        log_info "  URL:  http://localhost:$FRONTEND_PORT"
        log_info "  Logs: $PROJECT_ROOT/logs/frontend.log"
        return 0
    else
        log_error "Frontend failed to start"
        kill $pid 2>/dev/null
        return 1
    fi
}

stop_frontend() {
    kill_service "frontend"
}

