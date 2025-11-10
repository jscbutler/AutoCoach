#!/bin/bash
# Cloudflare Tunnel Management for AutoCoach
# Handles detection, configuration, and startup of the shared EVE/AutoCoach tunnel

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# Check if AutoCoach is configured in EVE tunnel
is_autocoach_in_eve_tunnel() {
    if [ ! -f "$EVE_TUNNEL_CONFIG" ]; then
        return 1
    fi
    
    grep -q "autocoach.eve-market.space" "$EVE_TUNNEL_CONFIG"
}

# Check if tunnel is running
is_tunnel_running() {
    process_running "cloudflared.*$EVE_TUNNEL_ID"
}

# Add AutoCoach to EVE tunnel config
add_autocoach_to_tunnel_config() {
    print_section "Adding AutoCoach to EVE Tunnel Config"
    
    if [ ! -f "$EVE_TUNNEL_CONFIG" ]; then
        print_error "EVE tunnel config not found: $EVE_TUNNEL_CONFIG"
        print_info "Setup EVE tunnel first from: $EVE_PROJECT"
        return 1
    fi
    
    # Backup original config
    cp "$EVE_TUNNEL_CONFIG" "$EVE_TUNNEL_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    print_success "Backed up EVE tunnel config"
    
    # Check if catch-all exists
    if ! grep -q "service: http_status:404" "$EVE_TUNNEL_CONFIG"; then
        print_error "Could not find catch-all rule in EVE config"
        return 1
    fi
    
    # Insert AutoCoach route before catch-all
    # Create a temporary file with the new config
    awk -v port="$AUTOCOACH_PORT" '
    /# Catch all \(required\)/ {
        print "  # AutoCoach API"
        print "  - hostname: autocoach.eve-market.space"
        print "    service: http://localhost:" port
        print ""
    }
    { print }
    ' "$EVE_TUNNEL_CONFIG" > "$EVE_TUNNEL_CONFIG.tmp"
    
    mv "$EVE_TUNNEL_CONFIG.tmp" "$EVE_TUNNEL_CONFIG"
    
    print_success "Added AutoCoach to EVE tunnel config"
    return 0
}

# Add DNS route for AutoCoach
add_dns_route() {
    print_section "Adding DNS Route"
    
    if ! command_exists cloudflared; then
        print_error "cloudflared not installed"
        return 1
    fi
    
    # Check if route already exists
    if cloudflared tunnel route dns list 2>/dev/null | grep -q "autocoach.eve-market.space"; then
        print_success "DNS route already exists"
        return 0
    fi
    
    print_info "Creating DNS route: autocoach.eve-market.space"
    if cloudflared tunnel route dns "$EVE_TUNNEL_ID" autocoach.eve-market.space; then
        print_success "DNS route created"
        return 0
    else
        print_error "Failed to create DNS route"
        return 1
    fi
}

# Start Cloudflare tunnel
start_tunnel() {
    print_section "Starting Cloudflare Tunnel"
    
    if ! command_exists cloudflared; then
        print_error "cloudflared not installed"
        print_info "Install with: brew install cloudflare/cloudflare/cloudflared"
        return 1
    fi
    
    if [ ! -f "$EVE_TUNNEL_CONFIG" ]; then
        print_error "EVE tunnel config not found"
        return 1
    fi
    
    # Start tunnel in background
    cd "$EVE_PROJECT" || return 1
    
    local log_file="$AUTOCOACH_ROOT/.logs/cloudflare-tunnel.log"
    mkdir -p "$(dirname "$log_file")"
    
    cloudflared tunnel --config config/cloudflare-tunnel.yaml run > "$log_file" 2>&1 &
    local tunnel_pid=$!
    
    store_pid "cloudflare_tunnel" "$tunnel_pid"
    
    sleep 3
    
    if process_running "cloudflared.*$EVE_TUNNEL_ID"; then
        print_success "Cloudflare tunnel started (PID: $tunnel_pid)"
        print_info "Log: $log_file"
        return 0
    else
        print_error "Tunnel failed to start"
        print_info "Check log: $log_file"
        return 1
    fi
}

# Main tunnel setup and start
setup_and_start_tunnel() {
    print_header "Cloudflare Tunnel Setup"
    
    # Check if tunnel is already running
    if is_tunnel_running; then
        print_success "Cloudflare tunnel already running"
        return 0
    fi
    
    # Check if AutoCoach is in tunnel config
    if ! is_autocoach_in_eve_tunnel; then
        print_warning "AutoCoach not configured in EVE tunnel"
        echo ""
        read -p "Add AutoCoach to EVE tunnel config? (y/n) " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if ! add_autocoach_to_tunnel_config; then
                return 1
            fi
            
            if ! add_dns_route; then
                print_warning "DNS route setup failed, but continuing..."
            fi
        else
            print_info "Skipping tunnel setup. AutoCoach will only be available on localhost."
            return 0
        fi
    else
        print_success "AutoCoach already in EVE tunnel config"
    fi
    
    # Start the tunnel
    if ! start_tunnel; then
        print_warning "Could not start tunnel automatically"
        print_info "You can start it manually from: $EVE_PROJECT"
        return 1
    fi
    
    return 0
}

# Export functions
export -f is_autocoach_in_eve_tunnel
export -f is_tunnel_running
export -f add_autocoach_to_tunnel_config
export -f add_dns_route
export -f start_tunnel
export -f setup_and_start_tunnel
