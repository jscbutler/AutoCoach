#!/bin/bash
# PostgreSQL management for AutoCoach

# Source common functions
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

check_postgres() {
    log_info "Checking PostgreSQL..."
    
    # Check if postgres is installed
    if ! command -v psql &> /dev/null; then
        log_warning "PostgreSQL not installed"
        log_info "Install with: brew install postgresql@14"
        return 1
    fi
    
    # Check if postgres is running
    if is_port_in_use $POSTGRES_PORT; then
        log_success "PostgreSQL is running on port $POSTGRES_PORT"
        return 0
    else
        log_warning "PostgreSQL not running"
        return 1
    fi
}

start_postgres() {
    log_header "Starting PostgreSQL"
    
    if check_postgres; then
        log_info "PostgreSQL already running, skipping"
        return 0
    fi
    
    log_info "Starting PostgreSQL..."
    
    # Try brew services first
    if command -v brew &> /dev/null; then
        brew services start postgresql@14 2>/dev/null || brew services start postgresql 2>/dev/null
        sleep 2
        
        if check_postgres; then
            log_success "PostgreSQL started successfully"
            return 0
        fi
    fi
    
    # Try pg_ctl if brew services failed
    if command -v pg_ctl &> /dev/null; then
        local data_dir="/usr/local/var/postgres"
        if [ -d "$data_dir" ]; then
            pg_ctl -D "$data_dir" start
            sleep 2
            
            if check_postgres; then
                log_success "PostgreSQL started successfully"
                return 0
            fi
        fi
    fi
    
    log_error "Failed to start PostgreSQL"
    log_info "Start manually with: brew services start postgresql"
    return 1
}

stop_postgres() {
    log_info "Note: PostgreSQL managed by system (not stopped by this script)"
    # We don't stop postgres as it may be used by other services
}

create_autocoach_db() {
    log_info "Checking AutoCoach database..."
    
    # Check if database exists
    if psql -lqt | cut -d \| -f 1 | grep -qw autocoach; then
        log_success "AutoCoach database exists"
        return 0
    else
        log_info "Creating AutoCoach database..."
        createdb autocoach 2>/dev/null
        
        if [ $? -eq 0 ]; then
            log_success "AutoCoach database created"
            return 0
        else
            log_error "Failed to create database"
            return 1
        fi
    fi
}

