# AutoCoach with Cloudflare Tunnel - Setup Guide

## Overview

This guide shows how to set up AutoCoach to use your existing `eve-market.space` domain infrastructure via Cloudflare Tunnel. This provides a **stable, permanent URL** for TrainingPeaks OAuth callbacks without needing localhost or changing callback URLs.

## Why Use Cloudflare Tunnel?

✅ **Permanent URL**: No more localhost limitations  
✅ **Professional**: Use your own domain (`autocoach.eve-market.space`)  
✅ **Secure**: HTTPS by default  
✅ **Reuses Infrastructure**: Leverages your existing EVE project setup  
✅ **No Port Forwarding**: Works behind NAT/firewall  
✅ **Free**: No additional costs (using existing tunnel)

## Prerequisites

- ✓ EVE Online project (`eve_py`) with Cloudflare tunnel already set up
- ✓ Domain `eve-market.space` configured in Cloudflare
- ✓ `cloudflared` installed on your machine
- ✓ Existing tunnel `eve-market-auth` from EVE project

## Quick Start

### Option A: Automated Setup (Recommended)

```bash
cd /Users/jeffbutler/Dev/AutoCoach

# 1. Run setup script
./scripts/setup_cloudflare_tunnel.sh

# 2. Start both tunnel and server
./scripts/start_with_tunnel.sh
```

Done! Your AutoCoach API is now at **https://autocoach.eve-market.space**

### Option B: Manual Setup

Follow the detailed steps below.

## Detailed Setup Steps

### Step 1: Configure Cloudflare Tunnel

The tunnel configuration reuses your existing `eve-market-auth` tunnel:

```bash
# Check if tunnel exists
cloudflared tunnel list | grep eve-market-auth
```

Expected output:
```
<tunnel-id>   eve-market-auth   ...
```

If tunnel doesn't exist, set it up from your EVE project first:
```bash
cd /Users/jeffbutler/Dev/Dev/eve_py
./scripts/setup_permanent_tunnel.sh
```

### Step 2: Add DNS Route for AutoCoach

```bash
# Add autocoach subdomain to existing tunnel
cloudflared tunnel route dns eve-market-auth autocoach.eve-market.space
```

This creates a DNS CNAME record pointing `autocoach.eve-market.space` to your tunnel.

### Step 3: Configure Environment

Edit `.env` file:

```bash
cd /Users/jeffbutler/Dev/AutoCoach
cp env.template .env
nano .env
```

Set the redirect URI to use the tunnel:

```bash
# OAuth Redirect URI - Use the Cloudflare tunnel URL
TRAININGPEAKS_REDIRECT_URI=https://autocoach.eve-market.space/auth/callback

# TrainingPeaks credentials (get from API portal)
TRAININGPEAKS_CLIENT_ID=your_client_id_here
TRAININGPEAKS_CLIENT_SECRET=your_client_secret_here

# Use sandbox for testing
TRAININGPEAKS_SANDBOX=true

# Server port
AUTOCOACH_PORT=8000
```

### Step 4: Update TrainingPeaks Application

1. Go to **https://api.trainingpeaks.com/request-access**
2. Edit your application settings
3. Update **Redirect URI** to: `https://autocoach.eve-market.space/auth/callback`
4. Save changes

⚠️ **Important**: The redirect URI must match exactly (including https://)

### Step 5: Start the Services

#### Terminal 1: Start Cloudflare Tunnel

```bash
cd /Users/jeffbutler/Dev/AutoCoach
cloudflared tunnel --config config/cloudflare-tunnel.yaml run eve-market-auth
```

You should see:
```
INF Connection established
INF Registered tunnel connection
INF Route registered for autocoach.eve-market.space
```

#### Terminal 2: Start FastAPI Server

```bash
cd /Users/jeffbutler/Dev/AutoCoach
source ac_env/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Or: Use the Combined Startup Script

```bash
./scripts/start_with_tunnel.sh
```

This runs both tunnel and server in one command!

### Step 6: Test the Setup

#### Test 1: Health Check

```bash
curl https://autocoach.eve-market.space/
```

Expected:
```json
{"status": "ok"}
```

#### Test 2: OAuth Initiation

Open browser:
```
https://autocoach.eve-market.space/auth/trainingpeaks?sandbox=true
```

Expected: JSON response with `authorization_url`

#### Test 3: Complete OAuth Flow

1. Copy the `authorization_url` from response
2. Paste in browser
3. Login to TrainingPeaks
4. Authorize AutoCoach
5. Should redirect to: `https://autocoach.eve-market.space/auth/callback?code=...`
6. Should see success message

### Step 7: Extract and Save Tokens

**While server is still running**, in a new terminal:

```bash
cd /Users/jeffbutler/Dev/AutoCoach
source ac_env/bin/activate
PYTHONPATH=. python scripts/get_tokens.py
```

Copy the tokens and add to `.env`:

```bash
TRAININGPEAKS_ACCESS_TOKEN=eyJhbGciOi...
TRAININGPEAKS_REFRESH_TOKEN=def50200a7f...
```

### Step 8: Verify Everything Works

```bash
PYTHONPATH=. python scripts/test_harness.py --tp-test
```

Expected output:
```
✓ TrainingPeaks client initialized
✓ Access token found
✓ Authenticated as: Your Name
✓ Thresholds retrieved
  FTP: 265W
```

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    TrainingPeaks OAuth Flow                       │
│                   (via Cloudflare Tunnel)                        │
└──────────────────────────────────────────────────────────────────┘

TrainingPeaks API
      ↓
      │ 1. User authorizes
      ↓
https://autocoach.eve-market.space/auth/callback?code=ABC123
      ↓
      │ Cloudflare Tunnel (eve-market-auth)
      ↓
localhost:8000/auth/callback
      ↓
      │ FastAPI Server (AutoCoach)
      ↓
Exchange code for tokens → Store in session
      ↓
Redirect to success page
```

## Tunnel Configuration

**File**: `config/cloudflare-tunnel.yaml`

```yaml
tunnel: eve-market-auth  # Reuse existing tunnel
credentials-file: /Users/jeffbutler/.cloudflared/eve-market-auth.json

ingress:
  - hostname: autocoach.eve-market.space
    service: http://localhost:8000
  
  - service: http_status:404
```

This configuration:
- Reuses the `eve-market-auth` tunnel from your EVE project
- Routes `autocoach.eve-market.space` → `localhost:8000`
- Shares credentials with EVE tunnel

## Shared Infrastructure

Your complete domain setup:

```
eve-market.space (root domain)
├── auth.eve-market.space         → EVE Auth API (port 5002)
├── autocoach.eve-market.space    → AutoCoach API (port 8000)
├── market.eve-market.space       → EVE Market Watch
├── industry.eve-market.space     → EVE Industry Finder
└── mineral.eve-market.space      → EVE Mineral Trader
```

**One tunnel serves all subdomains!**

## Troubleshooting

### "DNS record not found"

**Problem**: Domain hasn't propagated yet

**Solution**:
```bash
# Check DNS propagation
dig autocoach.eve-market.space

# Wait if no CNAME record shown, then try:
cloudflared tunnel route dns eve-market-auth autocoach.eve-market.space
```

### "Tunnel not found"

**Problem**: Tunnel doesn't exist

**Solution**:
```bash
# List tunnels
cloudflared tunnel list

# Create if needed (should exist from EVE project)
cd /Users/jeffbutler/Dev/Dev/eve_py
./scripts/setup_permanent_tunnel.sh
```

### "Connection refused"

**Problem**: Local server not running or wrong port

**Solution**:
```bash
# Check if server is running
lsof -i :8000

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### "Redirect URI mismatch"

**Problem**: Callback URL doesn't match TrainingPeaks settings

**Solution**:
1. Check `.env`: `TRAININGPEAKS_REDIRECT_URI`
2. Check TrainingPeaks portal: Application settings
3. Must match exactly: `https://autocoach.eve-market.space/auth/callback`
4. Restart server after changing `.env`

### Tunnel logs

```bash
# View tunnel logs
tail -f ~/.cloudflared/eve-market-auth.log

# Or if using start script:
tail -f /tmp/autocoach-tunnel.log
```

## Development vs Production

### Development (Localhost)

Use when developing locally without tunnel:

```bash
# .env
TRAININGPEAKS_REDIRECT_URI=http://localhost:8000/auth/callback

# TrainingPeaks portal
Redirect URI: http://localhost:8000/auth/callback

# Start
uvicorn app.main:app --reload
```

**Pros**: Faster iteration, simpler setup  
**Cons**: Must update TrainingPeaks callback each time

### Production (Cloudflare Tunnel)

Use for stable, long-term development:

```bash
# .env  
TRAININGPEAKS_REDIRECT_URI=https://autocoach.eve-market.space/auth/callback

# TrainingPeaks portal
Redirect URI: https://autocoach.eve-market.space/auth/callback

# Start
./scripts/start_with_tunnel.sh
```

**Pros**: Stable URL, professional, no config changes  
**Cons**: Requires tunnel running

## Running in Background

To keep tunnel running persistently:

```bash
# Using screen
screen -S autocoach-tunnel
cloudflared tunnel --config config/cloudflare-tunnel.yaml run eve-market-auth
# Press Ctrl+A, D to detach

# Using tmux
tmux new -s autocoach-tunnel
cloudflared tunnel --config config/cloudflare-tunnel.yaml run eve-market-auth
# Press Ctrl+B, D to detach

# Or as a systemd service (Linux) / LaunchAgent (macOS)
# See Cloudflare docs for service installation
```

## Cost & Limits

**Cloudflare Tunnel**: Free!

**Considerations**:
- No bandwidth limits for your use case
- Shared with EVE project (same tunnel)
- Domain costs (you already have eve-market.space)

## Security Notes

✅ **HTTPS by default** (Cloudflare provides SSL)  
✅ **Tokens not exposed** (server-side only)  
✅ **Firewall-friendly** (outbound connections only)  
✅ **No port exposure** (tunnel handles routing)  

⚠️ **Important**:
- Never commit `.env` file
- Keep tokens secure
- Use sandbox for testing
- Rotate tokens periodically

## Quick Command Reference

```bash
# Setup
./scripts/setup_cloudflare_tunnel.sh

# Start (combined)
./scripts/start_with_tunnel.sh

# Start (manual - Terminal 1)
cloudflared tunnel --config config/cloudflare-tunnel.yaml run eve-market-auth

# Start (manual - Terminal 2)
source ac_env/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Test connection
curl https://autocoach.eve-market.space/

# Get tokens (after OAuth)
PYTHONPATH=. python scripts/get_tokens.py

# Test TrainingPeaks
PYTHONPATH=. python scripts/test_harness.py --tp-test

# View tunnel logs
tail -f ~/.cloudflared/eve-market-auth.log

# Check tunnel status
cloudflared tunnel list
cloudflared tunnel info eve-market-auth
```

## Next Steps

After setup is complete:

1. ✅ Test OAuth flow
2. ✅ Extract and save tokens
3. ✅ Run test harness with `--tp-compare`
4. ✅ Compare sample workout with TrainingPeaks data
5. ✅ Build confidence in metrics calculations
6. 🚀 Start developing AutoCoach features!

## Related Documentation

- `TRAININGPEAKS_OAUTH_SETUP.md` - Complete OAuth guide
- `OAUTH_FLOW_DIAGRAM.md` - Visual OAuth flow
- `TEST_HARNESS_USAGE.md` - Test harness documentation
- `../eve_py/docs/PERMANENT_DOMAIN_SETUP.md` - Original tunnel setup

## Support

If you encounter issues:

1. Check tunnel logs: `tail -f ~/.cloudflared/eve-market-auth.log`
2. Verify DNS: `dig autocoach.eve-market.space`
3. Test local server: `curl http://localhost:8000/`
4. Check TrainingPeaks callback URL matches exactly
5. Ensure tunnel and server are both running

---

**Ready to go?** Run `./scripts/start_with_tunnel.sh` and start building! 🚀

