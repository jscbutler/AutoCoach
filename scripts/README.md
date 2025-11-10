# AutoCoach Scripts

Modular startup and management scripts for AutoCoach services.

## Quick Start

### Start All Services

```bash
./scripts/start_services.sh
```

This will:
- ✅ Check Cloudflare tunnel status (optional)
- ✅ Start PostgreSQL (if needed)
- ✅ Start FastAPI backend
- ✅ Start React frontend (when implemented)
- ✅ Show status dashboard

### Stop All Services

```bash
./scripts/stop_services.sh
```

## Main Scripts

| Script | Purpose |
|--------|---------|
| `start_services.sh` | **Main startup script** - starts all services |
| `stop_services.sh` | Stop all running services |
| `setup_cloudflare_tunnel.sh` | One-time Cloudflare tunnel setup |
| `get_tokens.py` | Extract OAuth tokens after authentication |

## Script Components

Modular components in `script_components/`:

| Component | Purpose |
|-----------|---------|
| `common.sh` | Shared functions, colors, logging, utilities |
| `cloudflare.sh` | Cloudflare tunnel detection and management |
| `postgres.sh` | PostgreSQL startup and database creation |
| `backend.sh` | FastAPI and backend services |
| `frontend.sh` | React frontend management |

## Service Ports

| Service | Port | Status |
|---------|------|--------|
| FastAPI Backend | 8000 | ✅ Active |
| React Frontend | 3010 | 🔮 Future |
| PostgreSQL | 5432 | ✅ Active |

## Adding New Services

### 1. Create Component Script

```bash
touch scripts/script_components/my_service.sh
chmod +x scripts/script_components/my_service.sh
```

### 2. Implement Functions

```bash
#!/bin/bash
# My service management

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

start_my_service() {
    log_header "Starting My Service"
    
    # Check if already running
    if is_port_in_use $MY_SERVICE_PORT; then
        log_warning "My Service already running"
        return 0
    fi
    
    # Start service
    log_info "Starting My Service..."
    my_service_command &
    local pid=$!
    
    # Wait and verify
    if wait_for_port $MY_SERVICE_PORT "My Service"; then
        add_pid "my_service" $pid
        log_success "My Service started (PID: $pid)"
        return 0
    else
        log_error "My Service failed to start"
        return 1
    fi
}

stop_my_service() {
    kill_service "my_service"
}
```

### 3. Add to start_services.sh

```bash
# Source the component
source "$SCRIPT_DIR/script_components/my_service.sh"

# Add to main() function
start_my_service
```

## Startup Sequence

```
1. Check Cloudflare Tunnel (optional, doesn't block)
   └─ Detects if EVE tunnel is running
   └─ Shows availability status
   
2. Start PostgreSQL
   └─ Checks if already running
   └─ Starts if needed (via brew services)
   └─ Creates autocoach database
   
3. Start FastAPI Backend
   └─ Activates virtual environment
   └─ Starts uvicorn on port 8000
   └─ Waits for health check
   
4. Start Frontend (when implemented)
   └─ Installs dependencies if needed
   └─ Starts React dev server on port 3010
   
5. Display Status Dashboard
   └─ Shows all service URLs
   └─ Shows log locations
   └─ Tails FastAPI logs
```

## Features

### Smart Service Detection

- **Skip if running**: Won't start services that are already running
- **Port checking**: Verifies services are actually listening
- **Process tracking**: Stores PIDs for clean shutdown

### Modular Architecture

- **Component-based**: Each service in its own file
- **Reusable functions**: Common utilities in `common.sh`
- **Easy to extend**: Add new services without touching existing code

### Graceful Shutdown

- **Ctrl+C handling**: Stops all services cleanly
- **PID tracking**: Kills all spawned processes
- **No orphans**: Cleans up properly

### Logging

- **Color-coded output**: Info (blue), Success (green), Warning (yellow), Error (red)
- **Log files**: Each service logs to `logs/` directory
- **Real-time tailing**: Main script tails FastAPI logs

## Environment Variables

Set in `.env` file or `script_components/common.sh`:

```bash
PROJECT_ROOT="/Users/jeffbutler/Dev/AutoCoach"
EVE_PROJECT="/Users/jeffbutler/Dev/Dev/eve_py"
AUTOCOACH_PORT=8000
FRONTEND_PORT=3010
POSTGRES_PORT=5432
TUNNEL_ID="5a4becbf-b84e-4e90-80d0-f4f8ec2ffc20"
```

## Troubleshooting

### Services won't start

```bash
# Check what's using the ports
lsof -i :8000
lsof -i :3010

# Kill existing processes
./scripts/stop_services.sh

# Try again
./scripts/start_services.sh
```

### Cloudflare tunnel not detected

```bash
# Check tunnel from EVE project
cd /Users/jeffbutler/Dev/Dev/eve_py
ps aux | grep cloudflared

# Start EVE tunnel if needed
# [use your EVE tunnel start script]

# AutoCoach will work on localhost without tunnel
```

### PostgreSQL won't start

```bash
# Check postgres status
brew services list | grep postgres

# Start manually
brew services start postgresql@14

# Check if running
psql -l
```

### Virtual environment issues

```bash
# Recreate virtual environment
rm -rf ac_env
python3 -m venv ac_env
source ac_env/bin/activate
pip install -r requirements.txt
```

## Development

### Testing a Component

```bash
# Source common functions
source scripts/script_components/common.sh
source scripts/script_components/backend.sh

# Test individual function
start_fastapi
```

### Debug Mode

Add `set -x` at the top of any script for verbose output:

```bash
#!/bin/bash
set -x  # Enable debug mode
```

## Legacy Scripts

These older scripts are now superseded by `start_services.sh`:

- `start_with_tunnel.sh` - Use `start_services.sh` instead
- `setup_trainingpeaks.sh` - Still useful for first-time OAuth setup

## Best Practices

### DO:
- ✅ Use `start_services.sh` for all development
- ✅ Add new services to component scripts
- ✅ Use common logging functions
- ✅ Check if services are running before starting
- ✅ Track PIDs for clean shutdown

### DON'T:
- ❌ Start services manually (hard to clean up)
- ❌ Modify main script for simple changes (use components)
- ❌ Skip error checking
- ❌ Forget to make scripts executable (`chmod +x`)
- ❌ Hardcode paths (use variables from `common.sh`)

## Future Enhancements

- [ ] Health check dashboard (live status updates)
- [ ] Service dependency management
- [ ] Docker integration
- [ ] CI/CD integration
- [ ] Background worker management
- [ ] Log rotation
- [ ] Performance monitoring

## Related Documentation

- `/docs/CLOUDFLARE_TUNNEL_SETUP.md` - Cloudflare tunnel configuration
- `/docs/TRAININGPEAKS_OAUTH_SETUP.md` - OAuth setup guide
- `/docs/ADD_TO_EVE_TUNNEL.md` - Adding AutoCoach to EVE tunnel
- `TEST_HARNESS_USAGE.md` - Test harness documentation

---

**Need help?** Check component scripts in `script_components/` for implementation details.
