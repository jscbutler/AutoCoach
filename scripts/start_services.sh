#!/bin/bash
# AutoCoach Service Orchestrator
# Starts all AutoCoach services in the correct order
#
# Usage:
#   ./scripts/start_services.sh              # Start all services
#   ./scripts/start_services.sh --no-tunnel  # Skip tunnel setup
#   ./scripts/start_services.sh --stop       # Stop all services

set -e

# Get script directory and load components
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPONENTS_DIR="$SCRIPT_DIR/script_components"

# Load component modules
source "$COMPONENTS_DIR/common.sh"
source "$COMPONENTS_DIR/cloudflare.sh"
source "$COMPONENTS_DIR/autocoach_server.sh"

# Parse arguments
START_TUNNEL=true
STOP_SERVICES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-tunnel)
            START_TUNNEL=false
            shift
            ;;
        --stop)
            STOP_SERVICES=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-tunnel    Skip Cloudflare tunnel setup"
            echo "  --stop         Stop all services"
            echo "  --help         Show this help message"
            echo ""
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Cleanup function
cleanup() {
    print_header "Shutting Down Services"
    
    stop_autocoach_server
    
    # Note: We don't stop the tunnel as it's shared with EVE
    print_info "Cloudflare tunnel left running (shared with EVE project)"
    
    cleanup_pids
    
    print_success "All AutoCoach services stopped"
    exit 0
}

# Stop services if requested
if [ "$STOP_SERVICES" = true ]; then
    cleanup
    exit 0
fi

# Set up signal handlers
trap cleanup INT TERM

# Main startup sequence
main() {
    print_header "AutoCoach Service Orchestrator"
    
    cd "$AUTOCOACH_ROOT" || exit 1
    
    # Create logs directory
    mkdir -p "$AUTOCOACH_ROOT/.logs"
    
    # Step 1: Cloudflare Tunnel
    if [ "$START_TUNNEL" = true ]; then
        if ! setup_and_start_tunnel; then
            print_warning "Tunnel setup incomplete, but continuing..."
            print_info "AutoCoach will be available on localhost only"
        fi
    else
        print_info "Skipping tunnel setup (--no-tunnel flag)"
    fi
    
    # Step 2: Future - PostgreSQL/TimescaleDB
    # TODO: Add PostgreSQL startup when database is set up
    # if ! start_postgres; then
    #     print_error "PostgreSQL failed to start"
    #     exit 1
    # fi
    
    # Step 3: AutoCoach FastAPI Server
    if ! start_autocoach_server; then
        print_error "AutoCoach server failed to start"
        cleanup
        exit 1
    fi
    
    # Step 4: Future - React Frontend
    # TODO: Add React frontend when UI is ready
    # if ! start_react_frontend; then
    #     print_error "React frontend failed to start"
    #     cleanup
    #     exit 1
    # fi
    
    # Summary
    print_header "✅ AutoCoach Services Started"
    
    echo "Service Status:"
    echo ""
    
    if is_tunnel_running; then
        print_success "Cloudflare Tunnel: Running"
        echo "  → https://autocoach.eve-market.space"
    else
        print_info "Cloudflare Tunnel: Not running (localhost only)"
    fi
    
    if is_server_running; then
        print_success "AutoCoach Server: Running on port $AUTOCOACH_PORT"
        echo "  → http://localhost:$AUTOCOACH_PORT"
        echo "  → http://localhost:$AUTOCOACH_PORT/docs (API docs)"
    fi
    
    echo ""
    echo "Quick Links:"
    echo "  Health:  http://localhost:$AUTOCOACH_PORT/"
    echo "  API Docs: http://localhost:$AUTOCOACH_PORT/docs"
    echo ""
    
    if is_tunnel_running; then
        echo "  Public:  https://autocoach.eve-market.space/"
        echo "  OAuth:   https://autocoach.eve-market.space/auth/trainingpeaks?sandbox=true"
        echo ""
    fi
    
    echo "Logs:"
    echo "  Server:  $AUTOCOACH_ROOT/.logs/autocoach-server.log"
    
    if is_tunnel_running; then
        echo "  Tunnel:  $AUTOCOACH_ROOT/.logs/cloudflare-tunnel.log"
    fi
    
    echo ""
    print_info "Press Ctrl+C to stop all services"
    echo ""
    
    # Keep script running
    while true; do
        sleep 1
        
        # Check if services are still running
        if ! is_server_running; then
            print_error "AutoCoach server stopped unexpectedly!"
            print_info "Check logs: $AUTOCOACH_ROOT/.logs/autocoach-server.log"
            cleanup
            exit 1
        fi
    done
}

# Run main
main
