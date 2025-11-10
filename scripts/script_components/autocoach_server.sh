#!/bin/bash
# AutoCoach FastAPI Server Management

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# Check if server is running
is_server_running() {
    port_in_use "$AUTOCOACH_PORT"
}

# Start AutoCoach FastAPI server
start_autocoach_server() {
    print_section "Starting AutoCoach Server"
    
    # Check if already running
    if is_server_running; then
        print_warning "AutoCoach server already running on port $AUTOCOACH_PORT"
        return 0
    fi
    
    # Check prerequisites
    if ! check_venv; then
        return 1
    fi
    
    check_env_file  # Warning only, not fatal
    
    # Activate virtual environment
    if ! activate_venv; then
        print_error "Failed to activate virtual environment"
        return 1
    fi
    
    # Start server
    cd "$AUTOCOACH_ROOT" || return 1
    
    local log_file="$AUTOCOACH_ROOT/.logs/autocoach-server.log"
    mkdir -p "$(dirname "$log_file")"
    
    print_info "Starting FastAPI server on port $AUTOCOACH_PORT..."
    
    uvicorn app.main:app --reload --host 0.0.0.0 --port "$AUTOCOACH_PORT" \
        > "$log_file" 2>&1 &
    
    local server_pid=$!
    store_pid "autocoach_server" "$server_pid"
    
    # Wait for server to be ready
    if wait_for_port "$AUTOCOACH_PORT" 10; then
        print_success "AutoCoach server started (PID: $server_pid)"
        print_info "Log: $log_file"
        
        # Test health endpoint
        if check_service_health "http://localhost:$AUTOCOACH_PORT/" 5; then
            print_success "Health check passed"
        else
            print_warning "Health check failed, but server is running"
        fi
        
        return 0
    else
        print_error "Server failed to start"
        print_info "Check log: $log_file"
        return 1
    fi
}

# Stop AutoCoach server
stop_autocoach_server() {
    print_section "Stopping AutoCoach Server"
    
    local pid=$(get_stored_pid "autocoach_server")
    
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        print_success "Stopped AutoCoach server (PID: $pid)"
    elif is_server_running; then
        kill_port "$AUTOCOACH_PORT"
        print_success "Stopped AutoCoach server on port $AUTOCOACH_PORT"
    else
        print_info "AutoCoach server not running"
    fi
}

# Export functions
export -f is_server_running
export -f start_autocoach_server
export -f stop_autocoach_server

