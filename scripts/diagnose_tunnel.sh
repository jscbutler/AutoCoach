#!/bin/bash
# Cloudflare Tunnel Diagnostics
# Run this to troubleshoot tunnel connectivity issues

echo "================================================================================"
echo "  Cloudflare Tunnel Diagnostics"
echo "================================================================================"
echo ""

TUNNEL_ID="5a4becbf-b84e-4e90-80d0-f4f8ec2ffc20"
EVE_CONFIG="/Users/jeffbutler/Dev/Dev/eve_py/config/cloudflare-tunnel.yaml"

# 1. Check if cloudflared is installed
echo "1. Checking cloudflared installation..."
if command -v cloudflared &> /dev/null; then
    VERSION=$(cloudflared --version 2>&1 | head -1)
    echo "   ✓ cloudflared installed: $VERSION"
else
    echo "   ✗ cloudflared NOT installed"
    echo "   Install: brew install cloudflare/cloudflare/cloudflared"
    exit 1
fi
echo ""

# 2. Check if tunnel process is running
echo "2. Checking if cloudflared process is running..."
if ps aux | grep -q "[c]loudflared.*$TUNNEL_ID"; then
    echo "   ✓ cloudflared process is running"
    ps aux | grep "[c]loudflared" | grep -v grep
else
    echo "   ✗ cloudflared process NOT running"
    echo "   This is likely the problem!"
fi
echo ""

# 3. Check tunnel configuration
echo "3. Checking tunnel configuration..."
if [ -f "$EVE_CONFIG" ]; then
    echo "   ✓ Config file exists: $EVE_CONFIG"
    echo ""
    echo "   Config contents:"
    cat "$EVE_CONFIG"
else
    echo "   ✗ Config file NOT found: $EVE_CONFIG"
fi
echo ""

# 4. Check tunnel info
echo "4. Checking tunnel info..."
cloudflared tunnel info "$TUNNEL_ID" 2>&1
echo ""

# 5. List all tunnels
echo "5. Listing all tunnels..."
cloudflared tunnel list 2>&1
echo ""

# 6. Check DNS routes
echo "6. Checking DNS routes..."
echo "   Running: cloudflared tunnel route dns list"
cloudflared tunnel route dns list 2>&1 | grep -E "(eve-market|autocoach)" || echo "   No routes found"
echo ""

# 7. Check credentials file
echo "7. Checking credentials file..."
CREDS_FILE="$HOME/.cloudflared/$TUNNEL_ID.json"
if [ -f "$CREDS_FILE" ]; then
    echo "   ✓ Credentials file exists: $CREDS_FILE"
else
    echo "   ✗ Credentials file NOT found: $CREDS_FILE"
fi
echo ""

# 8. Test DNS resolution
echo "8. Testing DNS resolution..."
for domain in eve-market.space auth.eve-market.space autocoach.eve-market.space; do
    echo "   $domain:"
    dig +short "$domain" 2>&1 | head -3 || echo "   Failed to resolve"
done
echo ""

# 9. Check recent logs
echo "9. Checking for recent tunnel logs..."
if [ -f "$HOME/.cloudflared/tunnel.log" ]; then
    echo "   Last 20 lines of tunnel.log:"
    tail -20 "$HOME/.cloudflared/tunnel.log"
elif [ -f "/tmp/cloudflare-tunnel.log" ]; then
    echo "   Last 20 lines of /tmp/cloudflare-tunnel.log:"
    tail -20 "/tmp/cloudflare-tunnel.log"
else
    echo "   No log files found in standard locations"
fi
echo ""

# 10. Recommended actions
echo "================================================================================"
echo "  Recommended Actions"
echo "================================================================================"
echo ""

if ! ps aux | grep -q "[c]loudflared.*$TUNNEL_ID"; then
    echo "❌ PROBLEM: Tunnel process is not running"
    echo ""
    echo "To start the tunnel:"
    echo "  cd /Users/jeffbutler/Dev/Dev/eve_py"
    echo "  cloudflared tunnel --config config/cloudflare-tunnel.yaml run"
    echo ""
    echo "Or use your existing EVE start script."
    echo ""
else
    echo "✓ Tunnel process is running"
    echo ""
    echo "If you're still getting Error 1033, try:"
    echo "  1. Stop the tunnel: pkill cloudflared"
    echo "  2. Wait 30 seconds"
    echo "  3. Start again: cloudflared tunnel --config $EVE_CONFIG run"
    echo "  4. Wait 1-2 minutes for DNS propagation"
    echo ""
fi

echo "Common Issues:"
echo "  • Tunnel running but wrong config → Restart with correct config"
echo "  • DNS not propagated yet → Wait 1-2 minutes after starting"
echo "  • Old tunnel process lingering → Kill all: pkill cloudflared, then restart"
echo "  • Credentials expired → Re-login: cloudflared tunnel login"
echo ""

