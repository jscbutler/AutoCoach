#!/bin/bash
# Test OAuth Setup for AutoCoach
# Verifies all components needed for TrainingPeaks OAuth

echo "================================================================================"
echo "  AutoCoach OAuth Setup Test"
echo "================================================================================"
echo ""

# Check if AutoCoach server is running
echo "1. Checking AutoCoach Server..."
if lsof -i :8000 &> /dev/null; then
    echo "   ✓ AutoCoach server running on port 8000"
    
    # Test health endpoint
    if curl -sf http://localhost:8000/ &> /dev/null; then
        RESPONSE=$(curl -s http://localhost:8000/)
        echo "   ✓ Health check: $RESPONSE"
    else
        echo "   ✗ Health check failed"
    fi
else
    echo "   ✗ AutoCoach server NOT running"
    echo ""
    echo "   Start it with:"
    echo "   cd /Users/jeffbutler/Dev/AutoCoach"
    echo "   ./scripts/start_services.sh"
    echo ""
    exit 1
fi
echo ""

# Check .env file
echo "2. Checking .env configuration..."
ENV_FILE="/Users/jeffbutler/Dev/AutoCoach/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "   ✗ .env file not found"
    echo ""
    echo "   Create it:"
    echo "   cd /Users/jeffbutler/Dev/AutoCoach"
    echo "   cp env.template .env"
    echo "   nano .env  # Add your TrainingPeaks credentials"
    echo ""
    exit 1
fi

echo "   ✓ .env file exists"

# Check for required variables
if grep -q "TRAININGPEAKS_CLIENT_ID=your_client_id_here" "$ENV_FILE"; then
    echo "   ⚠  CLIENT_ID not configured (still has template value)"
    NEEDS_CONFIG=true
fi

if grep -q "TRAININGPEAKS_CLIENT_SECRET=your_client_secret_here" "$ENV_FILE"; then
    echo "   ⚠  CLIENT_SECRET not configured (still has template value)"
    NEEDS_CONFIG=true
fi

REDIRECT_URI=$(grep "TRAININGPEAKS_REDIRECT_URI=" "$ENV_FILE" | cut -d'=' -f2)
if [ -n "$REDIRECT_URI" ]; then
    echo "   ✓ Redirect URI: $REDIRECT_URI"
else
    echo "   ⚠  Redirect URI not set"
    NEEDS_CONFIG=true
fi

if [ "$NEEDS_CONFIG" = true ]; then
    echo ""
    echo "   Configure your TrainingPeaks credentials in .env"
    echo "   Get them from: https://api.trainingpeaks.com/request-access"
    echo ""
fi
echo ""

# Check Cloudflare tunnel
echo "3. Checking Cloudflare Tunnel..."
if ps aux | grep -q "[c]loudflared.*5a4becbf"; then
    echo "   ✓ Cloudflare tunnel running"
    
    # Test public access
    echo "   Testing public access..."
    if curl -sf --max-time 5 https://autocoach.eve-market.space/ &> /dev/null; then
        echo "   ✓ Public URL accessible: https://autocoach.eve-market.space"
    else
        echo "   ⚠  Public URL not accessible yet (DNS may still be propagating)"
        echo "      Wait 1-2 minutes and try again"
    fi
else
    echo "   ⚠  Cloudflare tunnel not running"
    echo "      OAuth will work on localhost only"
    echo "      Redirect URI: http://localhost:8000/auth/callback"
fi
echo ""

# Test OAuth endpoints
echo "4. Testing OAuth Endpoints..."

# Test auth initiation endpoint
echo "   Testing /auth/trainingpeaks endpoint..."
AUTH_RESPONSE=$(curl -s http://localhost:8000/auth/trainingpeaks?sandbox=true 2>&1)

if echo "$AUTH_RESPONSE" | grep -q "authorization_url"; then
    echo "   ✓ OAuth initiation endpoint working"
    
    # Extract and show authorization URL
    if command -v jq &> /dev/null; then
        AUTH_URL=$(echo "$AUTH_RESPONSE" | jq -r '.authorization_url' 2>/dev/null)
        if [ "$AUTH_URL" != "null" ] && [ -n "$AUTH_URL" ]; then
            echo ""
            echo "   Authorization URL (first 80 chars):"
            echo "   ${AUTH_URL:0:80}..."
        fi
    fi
else
    echo "   ✗ OAuth initiation failed"
    echo ""
    echo "   Response:"
    echo "$AUTH_RESPONSE" | head -5
    echo ""
fi
echo ""

# Summary and next steps
echo "================================================================================"
echo "  Summary"
echo "================================================================================"
echo ""

ALL_GOOD=true

if ! lsof -i :8000 &> /dev/null; then
    echo "✗ AutoCoach server not running"
    ALL_GOOD=false
fi

if [ "$NEEDS_CONFIG" = true ]; then
    echo "⚠  TrainingPeaks credentials need configuration"
    ALL_GOOD=false
fi

if [ "$ALL_GOOD" = true ]; then
    echo "✅ OAuth setup looks good!"
    echo ""
    echo "Next Steps:"
    echo ""
    echo "1. Get TrainingPeaks API access:"
    echo "   https://api.trainingpeaks.com/request-access"
    echo ""
    echo "2. Update callback URL in TrainingPeaks portal:"
    if ps aux | grep -q "[c]loudflared.*5a4becbf"; then
        echo "   https://autocoach.eve-market.space/auth/callback"
    else
        echo "   http://localhost:8000/auth/callback"
    fi
    echo ""
    echo "3. Test OAuth flow:"
    if ps aux | grep -q "[c]loudflared.*5a4becbf"; then
        echo "   https://autocoach.eve-market.space/auth/trainingpeaks?sandbox=true"
    else
        echo "   http://localhost:8000/auth/trainingpeaks?sandbox=true"
    fi
    echo ""
    echo "4. Complete authorization in browser"
    echo ""
    echo "5. Extract tokens:"
    echo "   cd /Users/jeffbutler/Dev/AutoCoach"
    echo "   PYTHONPATH=. python scripts/get_tokens.py"
    echo ""
    echo "6. Test connection:"
    echo "   PYTHONPATH=. python scripts/test_harness.py --tp-test"
    echo ""
else
    echo "⚠  Some setup steps needed (see above)"
    echo ""
fi

echo "================================================================================"

