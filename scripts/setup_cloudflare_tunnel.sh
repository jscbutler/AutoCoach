#!/bin/bash
# Setup Cloudflare Tunnel for AutoCoach
# Adds AutoCoach to existing EVE tunnel (non-invasive)

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVE_PROJECT="/Users/jeffbutler/Dev/Dev/eve_py"
EVE_TUNNEL_CONFIG="$EVE_PROJECT/config/cloudflare-tunnel.yaml"
DOMAIN="autocoach.eve-market.space"

echo "================================================================================"
echo "  AutoCoach Cloudflare Tunnel Setup"
echo "================================================================================"
echo ""
echo "This will add AutoCoach to your existing EVE tunnel:"
echo "  → https://autocoach.eve-market.space"
echo ""
echo "⚠️  IMPORTANT: This modifies your EVE tunnel config (safely)"
echo "    We'll add ONE route for AutoCoach without affecting EVE routes"
echo "================================================================================"
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared not found!"
    echo ""
    echo "Install it with:"
    echo "  macOS: brew install cloudflare/cloudflare/cloudflared"
    echo "  Linux: wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    echo ""
    exit 1
fi

echo "✓ cloudflared is installed"
echo ""

# Check if EVE tunnel config exists
if [ ! -f "$EVE_TUNNEL_CONFIG" ]; then
    echo "❌ EVE tunnel config not found at:"
    echo "   $EVE_TUNNEL_CONFIG"
    echo ""
    echo "Set up your EVE tunnel first:"
    echo "  cd $EVE_PROJECT"
    echo "  ./scripts/setup_permanent_tunnel.sh"
    echo ""
    exit 1
fi

echo "✓ EVE tunnel config found"
echo ""

# Get tunnel ID from EVE config
TUNNEL_ID=$(grep "^tunnel:" "$EVE_TUNNEL_CONFIG" | awk '{print $2}')

if [ -z "$TUNNEL_ID" ]; then
    echo "❌ Could not read tunnel ID from EVE config"
    exit 1
fi

echo "✓ Tunnel ID: $TUNNEL_ID"
echo ""

# Check if AutoCoach already in config
if grep -q "autocoach.eve-market.space" "$EVE_TUNNEL_CONFIG"; then
    echo "✓ AutoCoach already configured in EVE tunnel"
else
    echo "⚠️  AutoCoach NOT in EVE tunnel config yet"
    echo ""
    echo "📝 Manual step required:"
    echo ""
    echo "Edit: $EVE_TUNNEL_CONFIG"
    echo ""
    echo "Add these lines BEFORE the catch-all (- service: http_status:404):"
    echo ""
    echo "  # AutoCoach API"
    echo "  - hostname: autocoach.eve-market.space"
    echo "    service: http://localhost:8000"
    echo ""
    echo "See full instructions: docs/ADD_TO_EVE_TUNNEL.md"
    echo ""
    read -p "Press Enter after you've added AutoCoach to the config..."
fi

# Check if DNS route already exists
echo ""
echo "Checking DNS route for $DOMAIN..."
EXISTING_ROUTE=$(cloudflared tunnel route dns list | grep "$DOMAIN" || echo "")

if [ -n "$EXISTING_ROUTE" ]; then
    echo "✓ DNS route already exists for $DOMAIN"
else
    echo "Adding DNS route..."
    cloudflared tunnel route dns "$TUNNEL_ID" "$DOMAIN"
    echo "✓ DNS route added: $DOMAIN → tunnel $TUNNEL_ID"
fi

echo ""
echo "================================================================================"
echo "✅ Setup Complete!"
echo "================================================================================"
echo ""
echo "Your AutoCoach API will be accessible at:"
echo "  https://autocoach.eve-market.space"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Update TrainingPeaks OAuth callback URL:"
echo "   → Go to: https://api.trainingpeaks.com/request-access"
echo "   → Set redirect URI: https://autocoach.eve-market.space/auth/callback"
echo ""
echo "2. Update AutoCoach .env file:"
echo "   TRAININGPEAKS_REDIRECT_URI=https://autocoach.eve-market.space/auth/callback"
echo ""
echo "3. Start/restart the tunnel (from EVE project):"
echo "   cd $EVE_PROJECT"
echo "   # Use your existing tunnel start script"
echo ""
echo "4. Start AutoCoach server (from AutoCoach project):"
echo "   cd $PROJECT_DIR"
echo "   source ac_env/bin/activate"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "5. Test OAuth flow:"
echo "   → Visit: https://autocoach.eve-market.space/auth/trainingpeaks?sandbox=true"
echo ""
echo "================================================================================"
echo "💡 Tips:"
echo "  • ONE tunnel serves both EVE and AutoCoach"
echo "  • EVE routes are unaffected"
echo "  • AutoCoach runs on port 8000 (no conflicts)"
echo "  • To remove: Delete 2 lines from EVE config + restart tunnel"
echo "================================================================================"
echo ""

