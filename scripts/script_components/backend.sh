#!/bin/bash
# Backend services management for AutoCoach

# Source common functions
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

start_fastapi() {
    log_header "Starting FastAPI Server"
    
    # Check if already running
    if is_port_in_use $AUTOCOACH_PORT; then
        log_warning "Port $AUTOCOACH_PORT already in use"
        log_info "Stop existing service or use a different port"
        return 1
    fi
    
    # Check prerequisites
    if ! check_venv; then
        return 1
    fi
    
    check_env_file  # Warning only, not fatal
    
    log_info "Starting FastAPI server on port $AUTOCOACH_PORT..."
    
    cd "$PROJECT_ROOT"
    activate_venv
    
    # Start server in background
    uvicorn app.main:app --reload --host 0.0.0.0 --port $AUTOCOACH_PORT > "$PROJECT_ROOT/logs/fastapi.log" 2>&1 &
    local pid=$!
    
    # Wait for server to start
    if wait_for_port $AUTOCOACH_PORT "FastAPI"; then
        add_pid "fastapi" $pid
        log_success "FastAPI server started (PID: $pid)"
        log_info "  Local:  http://localhost:$AUTOCOACH_PORT"
        log_info "  Docs:   http://localhost:$AUTOCOACH_PORT/docs"
        log_info "  Logs:   $PROJECT_ROOT/logs/fastapi.log"
        return 0
    else
        log_error "FastAPI server failed to start"
        log_info "Check logs: $PROJECT_ROOT/logs/fastapi.log"
        kill $pid 2>/dev/null
        return 1
    fi
}

stop_fastapi() {
    kill_service "fastapi"
}

# Future: OAuth service (if separate from FastAPI)
start_oauth_service() {
    log_info "OAuth service integrated with FastAPI"
    return 0
}

# Future: Other backend services
start_background_workers() {
    log_info "Background workers not yet implemented"
    return 0
}

